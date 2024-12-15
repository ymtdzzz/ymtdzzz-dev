---
title: Golangのzero-code auto instrumentation ２種食べ比べ
date: 2024-12-15
tags:
 - Go
 - OpenTelemetry
published: true
category: Observability
---

これは、[Qiita - OpenTelemetry Advent Calendar 2024](https://qiita.com/advent-calendar/2024/opentelemetry) 16日目の記事です。


# はじめに


これまでGoで書かれたアプリケーションをOpenTelemetryで計装するには、`net/http`や`redigo`、`database/sql`など各ライブラリ毎に対応する計装ライブラリを導入し差し替える必要がありました。これは、JavaやNodeJS、PHPといったzero-code計装が可能な言語に比べると導入ハードルが高くなる要因になり得そうです。


zero-code計装が難しい要因として、Golangがコンパイル言語であり実行時に計装用コードを差し込むことが困難なことが挙げられます。


しかし最近Golangのzero-code計装も盛り上がりを見せており、zero-code計装のための仕組みが生まれてきています。この記事では下記の２プロダクトを取り上げ、実際に使い心地を確かめてみます。

- [alibaba/opentelemetry-go-auto-instrumentation](https://github.com/alibaba/opentelemetry-go-auto-instrumentation/)（ビルド時に計装コードを差し込む）
- [open-telemetry/opentelemetry-go-instrumentation](https://github.com/open-telemetry/opentelemetry-go-instrumentation)（eBPFの仕組みを利用）

## 計装するサンプルアプリ


[ymtdzzz/go-auto-instrumentation-test](https://github.com/ymtdzzz/go-auto-instrumentation-test)


`server_a`と`server_b`という２つのアプリケーションを用意しました。`server_a`の`/call-b`エンドポイントにGETでアクセスすると、それぞれMySQLとRedisに適当なリクエストを投げつつ`server_b`の`/data`エンドポイントに内部的に通信が行われます。


また、`server_a`と`server_b`はそれぞれGinとEcho、環境変数を設定するとnet/httpでサーバーが起動するようにしています。


## 動作環境


動作確認は下記の環境で行いました。そのため、MacOSなど異なる環境では動作しない可能性があります。


![d61809db-f3ab-4818-a462-7eb44a3007f7.png](images/notionimages/notion/d61809db-f3ab-4818-a462-7eb44a3007f7.png)


# alibaba/opentelemetry-go-auto-instrumentation


１つ目は[alibaba/opentelemetry-go-auto-instrumentation](https://github.com/alibaba/opentelemetry-go-auto-instrumentation/)です。これはビルド時に計装用のコードを差し込むことでzero-code計装を可能にしています。


利用方法は簡単で、アプリケーションのビルド時に`go build`を叩く変わりに`otel go build`に差し替えてビルドを行うことでOpenTelemetry関連のコードを意識せずに計装を行うことができるようになります。


```docker
# Dockerfile.a_alibaba

# Install alibaba's auto instrumentation command
# NOTE: Quickly install sudo command because it's used in install.sh
RUN apt update \
  && apt install -y sudo \
  && curl -fsSL https://cdn.jsdelivr.net/gh/alibaba/opentelemetry-go-auto-instrumentation@main/install.sh | bash

RUN otel go build -o main ./server_a
```


ビルドされたバイナリの実行方法は特に変更は無く、また、サイドカーなども不要でスタンドアローンで動作します。


OpenTelemetry用の環境変数を設定して起動すれば、テレメトリが送信されます（今回のOTel Collectorはデバッグ用に[otel-tui](https://github.com/ymtdzzz/otel-tui)を利用します）。


```yaml
  # docker-compose.yml
  server_a_alibaba:
    build:
      context: .
      dockerfile: ./Dockerfile.a_alibaba
    ports:
      - "8080:8080"
    environment:
      # ...
      # OTel用の設定
      OTEL_EXPORTER_OTLP_ENDPOINT: "http://oteltui:4318"
      OTEL_EXPORTER_OTLP_INSECURE: true
      OTEL_SERVICE_NAME: server_a_alibaba
      
  oteltui:
    image: ymtdzzz/otel-tui:latest
    container_name: otel-tui
    stdin_open: true
    tty: true
```


`docker compose up`で環境を起動し、`http://localhost:8080/call-b`にアクセスすると、TraceやMetricが送信され始めます。


![f470fac3-c70e-43c0-b402-d1f98c36159e.png](images/notionimages/notion/f470fac3-c70e-43c0-b402-d1f98c36159e.png)


![5b15a164-7fa2-4d10-bce9-7b0d479e5b42.png](images/notionimages/notion/5b15a164-7fa2-4d10-bce9-7b0d479e5b42.png)


attributesの出力内容などは最後に比較しますが、sql以外は特にcontextを受け渡したりしていないのにも関わらずトレースがきちんと繋がっていることに驚きました（redisのdurationがマイナスになってるのはPINGのような一瞬で終わる処理だから？）。


```go
			// 元コードではcontextを渡していないが、きちんと繋がっている
			_, err := rdb.Do("PING") // this works even if we don't pass the context, wow!
			if err != nil {
				c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
				return
			}

			serverbURL := os.Getenv("SERVER_B_DATA_URL")
			resp, err := http.Get(serverbURL)
			if err != nil {
				c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
				return
			}
			defer resp.Body.Close()
```


また、ログについても、出力内容に`trace_id`と`span_id`がappendされていることがわかります。


![facd9862-bb59-4152-a771-13127fe4c9bb.png](images/notionimages/notion/facd9862-bb59-4152-a771-13127fe4c9bb.png)


テレメトリとしてLogを出すのは未対応っぽいですが、そこはマッピングできるので十分許容範囲な気がします。


## 簡単に実装を覗いてみる


詳細はリポジトリの[how-it-works.md](https://github.com/alibaba/opentelemetry-go-auto-instrumentation/blob/main/docs/how-it-works.md)を読むのが良さそうですが、簡単にご紹介します。


alibaba/opentelemetry-go-auto-instrumentationでは、Golangのtoolexecというビルド時に任意のコードを差し込むことでビルドプロセスを拡張する仕組みを利用し、計装用コードの差し込みをビルド時に行うようにしています。


依存パッケージやバージョンの解決など色々と複雑なことやっているように見えますので、そこはスルーしてまずは各パッケージ毎に用意されたruleを見てみます。


個人的にnet/httpのclientでcontextを渡していないのにきちんとトレースが繋がっているのが不思議だったので、[net/httpのrule](https://github.com/alibaba/opentelemetry-go-auto-instrumentation/tree/32af42919579fef40a724bf5fe6bb2a53455003e/pkg/rules/http)を見てみます。


まずは、ruleの設定ファイルを確認します。


```json
https://github.com/alibaba/opentelemetry-go-auto-instrumentation/blob/32af42919579fef40a724bf5fe6bb2a53455003e/pkg/data/default.json#L388-L395
  {
    "ImportPath": "net/http",
    "Function": "RoundTrip",
    "ReceiverType": "*Transport",
    "OnEnter": "clientOnEnter",
    "OnExit": "clientOnExit",
    "Path": "github.com/alibaba/opentelemetry-go-auto-instrumentation/pkg/rules/http"
  },
```


パッケージのimport pathやhookしたい対象のfunctionを指定しているようです。また、OnEnterとOnExitで指定されている関数が差し込む処理っぽいので、そこを探してみます。


```go
// https://github.com/alibaba/opentelemetry-go-auto-instrumentation/blob/32af42919579fef40a724bf5fe6bb2a53455003e/pkg/rules/http/client_setup.go#L29-L48
func clientOnEnter(call api.CallContext, t *http.Transport, req *http.Request) {
	if netHttpFilter.FilterUrl(req.URL) {
		return
	}
	netHttpRequest := &netHttpRequest{
		method: req.Method,
		url:    req.URL,
		header: req.Header,
		host:   req.Host,
		isTls:  req.TLS != nil,
	}
	netHttpRequest.version = getProtocolVersion(req.ProtoMajor, req.ProtoMinor)
	ctx := netHttpClientInstrumenter.Start(req.Context(), netHttpRequest)
	req = req.WithContext(ctx)
	call.SetParam(1, req)
	data := make(map[string]interface{}, 1)
	data["ctx"] = ctx
	call.SetData(data)
	return
}
```


読み込みが足りておらず`call`の実体までは理解できていませんが、Request内容を`netHttpClientInstrumenter`に渡し、戻ってきた`ctx`を`req`に詰めているようです。恐らくTrace Contextの生成は`netHttpClientInstrumenter` でやってそうなので、そちらも覗いてみます。


```go
// https://github.com/alibaba/opentelemetry-go-auto-instrumentation/blob/32af42919579fef40a724bf5fe6bb2a53455003e/pkg/rules/http/net_http_otel_instrumenter.go#L201C1-L219C2
func BuildNetHttpClientOtelInstrumenter() *instrumenter.PropagatingToDownstreamInstrumenter[*netHttpRequest, *netHttpResponse] {
	builder := &instrumenter.Builder[*netHttpRequest, *netHttpResponse]{}
	clientGetter := netHttpClientAttrsGetter{}
	commonExtractor := http.HttpCommonAttrsExtractor[*netHttpRequest, *netHttpResponse, http.HttpClientAttrsGetter[*netHttpRequest, *netHttpResponse], net.NetworkAttrsGetter[*netHttpRequest, *netHttpResponse]]{HttpGetter: clientGetter, NetGetter: clientGetter}
	networkExtractor := net.NetworkAttrsExtractor[*netHttpRequest, *netHttpResponse, net.NetworkAttrsGetter[*netHttpRequest, *netHttpResponse]]{Getter: clientGetter}
	return builder.Init().SetSpanStatusExtractor(http.HttpClientSpanStatusExtractor[*netHttpRequest, *netHttpResponse]{Getter: clientGetter}).SetSpanNameExtractor(&http.HttpClientSpanNameExtractor[*netHttpRequest, *netHttpResponse]{Getter: clientGetter}).
		SetSpanKindExtractor(&instrumenter.AlwaysClientExtractor[*netHttpRequest]{}).
		AddOperationListeners(http.HttpClientMetrics(), http.HttpClientMetrics()).
		SetInstrumentationScope(instrumentation.Scope{
			Name:    utils.NET_HTTP_CLIENT_SCOPE_NAME,
			Version: version.Tag,
		}).
		AddAttributesExtractor(&http.HttpClientAttrsExtractor[*netHttpRequest, *netHttpResponse, http.HttpClientAttrsGetter[*netHttpRequest, *netHttpResponse], net.NetworkAttrsGetter[*netHttpRequest, *netHttpResponse]]{Base: commonExtractor, NetworkExtractor: networkExtractor}).BuildPropagatingToDownstreamInstrumenter(func(n *netHttpRequest) propagation.TextMapCarrier {
		if n.header == nil {
			return nil
		}
		return propagation.HeaderCarrier(n.header)
	}, otel.GetTextMapPropagator())
}
```


RequestからテレメトリのAttributeにセットするための情報を取得するExtractorが定義されています。処理の実体は`*instrumenter.PropagatingToDownstreamInstrumenter`みたいなので、もうちょい掘ってみます。


```go
// https://github.com/alibaba/opentelemetry-go-auto-instrumentation/blob/32af42919579fef40a724bf5fe6bb2a53455003e/pkg/inst-api/instrumenter/instrumenter.go#L48-L52
type PropagatingToDownstreamInstrumenter[REQUEST any, RESPONSE any] struct {
	carrierGetter func(REQUEST) propagation.TextMapCarrier
	prop          propagation.TextMapPropagator
	base          InternalInstrumenter[REQUEST, RESPONSE]
}
```


さらに`InternalInstrumenter`を確認します。


```go
// https://github.com/alibaba/opentelemetry-go-auto-instrumentation/blob/32af42919579fef40a724bf5fe6bb2a53455003e/pkg/inst-api/instrumenter/instrumenter.go#L89-L115
func (i *InternalInstrumenter[REQUEST, RESPONSE]) doStart(parentContext context.Context, request REQUEST, timestamp time.Time, options ...trace.SpanStartOption) context.Context {
	if i.enabler != nil && !i.enabler.Enable() {
		return parentContext
	}
	for _, listener := range i.operationListeners {
		parentContext = listener.OnBeforeStart(parentContext, timestamp)
	}
	// extract span name
	spanName := i.spanNameExtractor.Extract(request)
	spanKind := i.spanKindExtractor.Extract(request)
	options = append(options, trace.WithSpanKind(spanKind))
	newCtx, span := i.tracer.Start(parentContext, spanName, options...)
	attrs := make([]attribute.KeyValue, 0, 20)
	// extract span attrs
	for _, extractor := range i.attributesExtractors {
		attrs, newCtx = extractor.OnStart(attrs, newCtx, request)
	}
	// execute context customizer hook
	for _, customizer := range i.contextCustomizers {
		newCtx = customizer.OnStart(newCtx, request, attrs)
	}
	for _, listener := range i.operationListeners {
		newCtx = listener.OnBeforeEnd(newCtx, attrs, timestamp)
	}
	span.SetAttributes(attrs...)
	return i.spanSuppressor.StoreInContext(newCtx, spanKind, span)
}
```


どうやらここが計装処理の実体のようです。ここでtraceをスタートし、先程定義して設定したExtractorを呼び出してAttributeなどにセットしているようです。そして、最後に新たなcontextを返却しています。


ruleの設定ファイルを作成し、それに合わせて必要なExtractorを定義してあげることで、他のパッケージでも自由にzero-codeすることができそうですね。


[ドキュメント](https://github.com/alibaba/opentelemetry-go-auto-instrumentation/blob/main/docs/how-to-add-a-new-rule.md)ではos.Getenv()のruleを作成する簡単な事例も紹介されていますので、興味のある方はご参照ください。


# open-telemetry/opentelemetry-go-instrumentation


続いて[open-telemetry/opentelemetry-go-instrumentation](https://github.com/open-telemetry/opentelemetry-go-instrumentation)です。こちらは先程とは異なり、eBPFの仕組みを利用したzero-code計装の試みとなります。eBPFについては私自身あまり詳しくないですが、ユーザー領域で実行中のプログラム（プロセス）に対して特定のコードをアタッチする仕組みです。


ではとりあえず使ってみます。ただし、この仕組みでは対応パッケージが少なく（後述）、HTTPサーバーはnet/httpのみ対応しているため、サンプルアプリケーションでは実装を切り替えています。


```yaml
  # docker-compose.yml
  server_a_otel:
    build:
      context: .
      dockerfile: ./Dockerfile.a_otel
    ports:
      - "8082:8080"
    environment:
      # ...
      SERVER_MODE: "net/http" # ここで切り替え
    depends_on:
      - redis
      - mysql
    volumes:
      - server_a_otel_binary:/app
```


また、こちらの仕組みはeBPFプログラムをサイドカーとして動かします。そのため、docker composeで計装するためには実行ファイルとプロセス情報取得用に`/proc` をマウントする必要があります。


```yaml
  # docker-compose.yml
  server_a_otel_agent:
    image: otel/autoinstrumentation-go
    privileged: true
    pid: "host"
    environment:
      OTEL_EXPORTER_OTLP_ENDPOINT: "http://oteltui:4318"
      OTEL_EXPORTER_OTLP_INSECURE: true
      OTEL_GO_AUTO_TARGET_EXE: /app/main_a # マウントした実行ファイルを指定
      OTEL_SERVICE_NAME: server_a_otel
      OTEL_PROPAGATORS: tracecontext,baggage
      OTEL_GO_AUTO_INCLUDE_DB_STATEMENT: true
      OTEL_GO_AUTO_PARSE_DB_STATEMENT: true
    volumes:
      - server_a_otel_binary:/app # 計装対象のコンテナとシェアしている実行ファイルのvolume
      - /proc:/host/proc
    depends_on:
      - server_a_otel
     
volumes:
  server_a_otel_binary:
```


先程と同様にdocker composeで起動後`http://localhost:8082/call-b`にアクセスするとトレースが収集できます。


![f46a9da4-e2c4-40b3-aba6-cb37b82b2cf2.png](images/notionimages/notion/f46a9da4-e2c4-40b3-aba6-cb37b82b2cf2.png)


こちらもきちんとトレースが繋がっていますね。なお、Redisクライアントについてはサポートされていないためトレースは出力されません。


この方法の注意点としては、コード内できちんとcontextを引き回す実装になっていないとトレースが途切れてしまう点です。


なお、仕組みや実装については時間の都合上省略します（全然読めていない）。詳細は[How it works](https://github.com/open-telemetry/opentelemetry-go-instrumentation/blob/main/docs/how-it-works.md)をご参照ください。


# 両者の比較


軽く触っただけではありますが、両者を簡単に比較してみます。


## 対応パッケージ


対応パッケージはalibabaの方が充実してますね。また、logやslog, zapなどのLoggerにも対応しているのもありがたいです。


| ライブラリ         | alibaba | otel |
| ------------- | ------- | ---- |
| database/sql  | ○       | ○    |
| echo          | ○       | ☓    |
| elasticsearch | ○       | ☓    |
| fasthttp      | ○       | ☓    |
| gin           | ○       | ☓    |
| go-redis      | ○       | ☓    |
| gorm          | ○       | ☓    |
| grpc          | ○       | ○    |
| hertz         | ○       | ☓    |
| kratos        | ○       | ☓    |
| log           | ○       | ☓    |
| logrus        | ○       | ☓    |
| mongodb       | ○       | ☓    |
| mux           | ○       | ☓    |
| net/http      | ○       | ○    |
| redigo        | ○       | ☓    |
| slog          | ○       | ☓    |
| zap           | ○       | ☓    |
| fiber         | ○       | ☓    |
| kafka-go      | ☓       | ○    |


## 拡張性


alibabaのビルド時に差し込む方式についてはJSONとGolangでRuleを定義することで拡張が可能です。また、結局はコードの差し替えになるためcontextの差し替えなどRuleの柔軟性も高そうで、すでに充実していますが、今後色々なパッケージが対応されそうな気配を感じます。


対してOTelのeBPF方式は、probeの実装にC言語が利用されるためeBPFそれ自体へのキャッチアップも含めてハードルは高そうに思われました。（逆にその辺りに詳しい人だったらどんどん拡張できるのかなぁ？）


あくまでもGolangの土俵で　と考えるとalibaba方式に軍配が上がるかもしれません。


## 利用しやすさ


どちらも導入は楽でした。alibabaのビルド方式はビルドコマンドの差し替え、otelのeBPF方式はサイドカーで実行ファイルとプロセスの共有できればシュッと導入できます。


ただ、eBPFの場合強めの権限を割り当てる必要があったり、共有ボリュームのマウントなどはハードルになる側面があるかもしれません。


## 事故りにくさ


実行ファイルへの影響度、実行時エラーの起こりにくさについてはプロセスが分離しているeBPFの方が良さそうです。


ビルド方式でもエラーハンドリングは丁寧に行っておりメイン処理に影響を与えないような配慮はしてそうでしたが、柔軟なruleが作成できる分悪い影響を与えてしまうリスクはあるように思えます（それを言うなら計装ライブラリみんなそうですが）。


## パフォーマンス


ベンチマークはとってないので今回は言及できません。構成も全然違うので何もわからない。


# さいごに


どちらも実験的なフェーズではあると思いますが普通にちゃんとテレメトリ出ているので「ついにGolangにもzero-code計装の時代がやってきたか・・・！」と思いました。


個人的にalibabaのビルド方式はtoolexecというGolangの仕組みに上手に乗っかっている感じがしてとても好きです。引き続きzero-code計装界隈はwatchしていこうと思います！

