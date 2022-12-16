---
title: 【OpenTelemetry】カスタムPropagatorでバッチや非同期処理のTraceを行う
date: 2022-12-16
tags:
 - OpenTelemetry
 - Go
 - RabbitMQ
published: true
category: Observability
---

こんにちは、[@ymtdzzz](https://twitter.com/ymtdzzz)です。


この記事は[OpenTelemetry Advent Calendar 2022](https://qiita.com/advent-calendar/2022/opentelemetry)の16日目の記事です。14日目はlufiabbさんの「[Goで実装したアプリケーションのメトリックをOpenTelemetryで計装する](https://blog.lufia.org/entry/2022/12/14/190110)」でした。


今回はpropagatorを自前で用意してキューを挟んだ非同期処理をトレースする方法について見ていこうと思います。


# Table of Contents


# モチベーション


最近所属会社ではSLI/SLOの導入が進んでいますが、基盤系システムをきちんと計測してSLOに落とし込むのが難しく感じています。
例えば通知システムの場合、多くはメッセージブローカーを経由して非同期で処理することが多いと思いますが、その際、

- 通知イベントが発生して、実際にエンドユーザーに通知が届くまでの時間
- 通知ライフサイクル全体のエラー率

など、必要なメトリクスを収集するためには独自の追跡手段を確立する必要があります。
（実際はそういった非同期系の処理についてはSLI/SLOは適用できていないですが、今後もしやるならという仮定）


そこで、OpenTelemetryで良い感じに測定・追跡できるようにしたいと思ったのがきっかけです。


# サンプルケース


リポジトリはこちら


[https://github.com/ymtdzzz/batch-tracing-sample](https://github.com/ymtdzzz/batch-tracing-sample)


（実行方法などはREADME参照。`docker compose up -d`で上がります）


今回は下記のような構成を例にしてみます。


![6aa06c90-31bd-493e-8bfb-c2058beab013.jpeg](../../../../gridsome-theme/src/assets/images/notion/6aa06c90-31bd-493e-8bfb-c2058beab013.jpeg)

- バッチ処理で通知内容をメッセージとしてキューイング（RabbitMQ）
- consumer（worker）がメッセージを受信して、通知用HTTPサーバーをcall（email or push）
- **通知サーバーでは一定の確率でエラーが発生**

それぞれ手動計装と、HTTP client&serverについては自動計装で対応しているので、context propagationでポイントとなるのは「batch（producer）→RabbitMQ→worker（consumer）」の部分になります。


## 課題


非同期部分のpropagationをやらずにトレースすると下記の通り、batchとその後のworkerのトレースが関連付けられません（それはそう）。


![289b5e81-7eec-4a8b-810b-9e03cc121952.png](../../../../gridsome-theme/src/assets/images/notion/289b5e81-7eec-4a8b-810b-9e03cc121952.png)


![36b4a946-7fa6-454d-8e15-471463ef5fcc.png](../../../../gridsome-theme/src/assets/images/notion/36b4a946-7fa6-454d-8e15-471463ef5fcc.png)


![d2fcfbd7-80ca-4723-9c00-2693eb4273ab.jpeg](../../../../gridsome-theme/src/assets/images/notion/d2fcfbd7-80ca-4723-9c00-2693eb4273ab.jpeg)


しかも、Golangの場合はRabbitMQ対応のinstrumentation libraryも無さそうです。


[https://opentelemetry.io/registry/?s=rabbitmq&component=&language=](https://opentelemetry.io/registry/?s=rabbitmq&component=&language=)


## ではどうすればいいのか


HTTPやgRPCのような同期型のメッセージングであっても、今回のような非同期型であってもcontext propagationの基本はpropagatorです。


メッセージにcontextを乗せられるように、propagatorを実装すれば良いのです。


# RabbitMQ用のpropagator実装


## propagatorの仕組み


[https://opentelemetry.io/docs/reference/specification/context/api-propagators/](https://opentelemetry.io/docs/reference/specification/context/api-propagators/)


propagatorは、その名の通りcontextをプロセス間で受け渡しするための仕組みをAPIに落としこんだものです。


context propagationは、contextを何らかの形でプロセス間のメッセージの中に注入（Inject）し、受信側はそのメッセージからcontextを抽出（Extract）することで実現されますが、その注入方法と抽出方法を定義したものになります。また、各propagatorはcarrierを持っており、それが実際のInject/Extractを担当します。


幸いにもRabbitMQにはメッセージにkey-value形式の`Headers`を入れることができる（[doc](https://www.rabbitmq.com/publishers.html#message-properties)）ので、`TextMapPropagator`を使ってcontext propagationできそうです。図にすると下記の通りです。


![66de15ed-1965-4602-ab96-e4f8c1cf4176.jpeg](../../../../gridsome-theme/src/assets/images/notion/66de15ed-1965-4602-ab96-e4f8c1cf4176.jpeg)


## propagator実装


TextMapへの操作を行っているのはCarrierなので、厳密に言うとpropagatorを実装するというわけでは無く、Carrierのinterfaceを満たしたstructを定義してあげれば良いのです。


interface定義は[こちら](https://pkg.go.dev/go.opentelemetry.io/otel@v1.11.2/propagation#TextMapCarrier)


```go
type TextMapCarrier interface {

	// Get returns the value associated with the passed key.
	Get(key string) string

	// Set stores the key-value pair.
	Set(key string, value string)

	// Keys lists the keys stored in this carrier.
	Keys() []string
}
```


このinterfaceを満たしたCarrier実装（[ソース](https://github.com/ymtdzzz/batch-tracing-sample/blob/main/notification-manager/internal/carrier.go)）


```go
type AMQPCarrier struct {
	headers amqp.Table
}

func (c *AMQPCarrier) Get(key string) string {
	return fmt.Sprintf("%s", c.headers[key])
}

func (c *AMQPCarrier) Set(key string, value string) {
	c.headers[key] = value
}

func (c *AMQPCarrier) Keys() []string {
	keys := make([]string, len(c.headers))
	for k := range c.headers {
		keys = append(keys, k)
	}
	return keys
}
```


`amqp.Table`は`map[string]interface{}`なので、`Get()`がちょっと雑ですが、サンプル実装用途なら良いでしょう。


## 送信側の実装


あとはpropagatorでheaderにcontextをセットさせて、メッセージ送信すればOKです（[ソース](https://github.com/ymtdzzz/batch-tracing-sample/blob/main/notification-manager/cmd/batch/main.go#L124-L142)）


```go
	// 空amqp.Tablesの生成
	headers := amqp.NewConnectionProperties()	
	// 自作carrierに登録
	carrier := internal.NewAMQPCarrier(headers)
	// contextをInject
	otel.GetTextMapPropagator().Inject(ctx, carrier)
	err = ch.PublishWithContext(
		ctx,
		"",
		q.Name,
		false,
		false,
		amqp.Publishing{
			ContentType: "application/octet-stream",
			Body:        msg,
			Headers:     headers, // Inject済みheaderをセット
		},
	)
	if err != nil {
		panic(err)
	}
	log.Println("Message has been sent")
```


## 受信側の実装


受信側も同様です（[ソース](https://github.com/ymtdzzz/batch-tracing-sample/blob/main/notification-manager/cmd/worker/main.go#L107-L119)）


```go
		// 自作carrierに受信したheaderを登録
		carrier := internal.NewAMQPCarrier(d.Headers)
		// contextをExtract
		ctx := otel.GetTextMapPropagator().Extract(context.Background(), carrier)
		// 受信したcontextを親Spanとして子Span生成
		ctx, span := otel.Tracer("notification").Start(ctx, "consume")

		msg, err := internal.DecodeNotificationMessage(d.Body)
		if err != nil {
			panic(err)
		}
		log.Printf("received msg: %v\n", msg)

		internal.CallServer(ctx, &client, msg)

		span.End()
```


# トレースできた🎉


実装が完了したので動かしてみると、ちゃんとSpanが繋がっています🎉


![b85ead1f-1ccd-4b99-a180-983592a6fd5b.png](../../../../gridsome-theme/src/assets/images/notion/b85ead1f-1ccd-4b99-a180-983592a6fd5b.png)


トレースが繋がったことで、server側でエラーが発生した処理の起点となったbatch処理がどれなのかが遡ることも可能になりました。


![397ec0a6-ae3a-4e36-b25a-fa135fdf9c2d.png](../../../../gridsome-theme/src/assets/images/notion/397ec0a6-ae3a-4e36-b25a-fa135fdf9c2d.png)


Trace全体のdurationが計測できるようになったので、通知速度劣化時のボトルネック解析や、そもそも通知が遅くなったことをユーザー体験ベース（メッセージ滞留とかではなく）で気付けるようになりました。


# おわりに


いかがでしたでしょうか。


個人的には非同期通信とかバッチ系のトレースはSpan Link等を使って限定的にSpan繋ぐ程度しかできないと考えていましたが、propagatorのおかげでメッセージングのプロトコルに縛られずにトレースできることがわかりました。


非同期処理のトレーシングで悩んでいた方や、Propagator is 何？状態の人の参考になれば幸いです！


次回は[@symmr](https://qiita.com/symmr)さんです！

