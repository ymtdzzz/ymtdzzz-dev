---
title: OpenTelemetryとOpencensusを共存させる
date: 2023-02-12
tags:
 - OpenTelemetry
 - OpenCensus
 - Tracing
 - APM
 - Go
published: true
category: Observability
---

最近Spanner周りのレイテンシーが気にあることがあり、とりあえずgRPCのTracerを入れてみたはいいものの、イマイチしっくり来る情報が取れませんでした。


もともとSpanner clientには[OpenCensusによるトレーシングがすでに実装されています](https://pkg.go.dev/cloud.google.com/go/spanner#hdr-Tracing)が、アプリのトレーシングで使用しているFWがOpenTelemetryだったので仕方なくotelgrpcを使用してお茶を濁していたのですが、特にSpanner固有のイベント（トランザクションのリトライとか）を確認できればもう少し深い洞察ができそうだなと思い、共存する方法を調査しました。


# Bridge


今回のように「OpenTelemetry使ってるけど一部OpenCensusでinstrumentされたライブラリを使っている」（**逆もしかり**）なケースで使えるのがTrace Bridgeです。


[https://opentelemetry.io/docs/reference/specification/compatibility/opencensus/#trace-bridge](https://opentelemetry.io/docs/reference/specification/compatibility/opencensus/#trace-bridge)


これは簡単にいうと、OpenCensusのAPIをラップすることで、実装側を変えず（これまで通りOpenCensusでinstrumentしたままで）OpenTelemetryにトレースを送信することができます。


ただし、TraceFlagの扱いやリンクなど、互換性の無いor異なる仕様についてはうまくトレースできないので注意が必要です。詳細は下記を参照。


[https://opentelemetry.io/docs/reference/specification/compatibility/opencensus/#known-incompatibilities](https://opentelemetry.io/docs/reference/specification/compatibility/opencensus/#known-incompatibilities)


# 実際にやってみる


ということで実際にやってみます。


サンプル実装：[https://github.com/ymtdzzz/otel-and-opencensus-sample](https://github.com/ymtdzzz/otel-and-opencensus-sample)


## Tracerの初期化時にbridgeの設定を行う


```go
import (
	octrace "go.opencensus.io/trace"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/bridge/opencensus"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	// ...
)

// bridgeの設定
bridge := otel.GetTracerProvider().Tracer("opencensus-bridge")
octrace.DefaultTracer = opencensus.NewTracer(bridge)
```


差分としてはこれだけです。otelのTracerを取得してTracer Bridgeを生成（`opencensus.NewTracer()`）し、OpenCensusの`DefaultTracer`に設定してあげます。


## 動作確認


今回はSpannerで、同一行を並列に１０本同時更新する処理で試してみました。


![caca0b28-3329-4563-8a1a-704f13192adb.png](../../../../gridsome-theme/src/assets/images/notion/caca0b28-3329-4563-8a1a-704f13192adb.png)


ほぼ確実にabort&retryが走るので全体で3sくらいかかっています。


ReadWriteTransactionのSpanにイベントとしていくつかSpanner固有の情報が載ってきているのがわかります。


```go
Acquiring a session
Acquired session
Starting transaction attempt
Backing off after ABORTED for 13.469032ms, then retrying
Starting transaction attempt
```


ここから、一度abortされ、リトライで成功していることがわかります。


# さいごに


各Spanの情報はotelgrpcでinstrumentしても同じような結果になりそうですが、Spanner client特有のイベントも確認できるのでclientのinstrumentationを利用した方が良さそうです。


また、今後clientがOpenTelemetryによるトレースをサポートするようになっても、前述のbridge関連の初期化処理を削除するだけで済むので、完全移行もスムーズに行きそうですね。


# 参考


[bridge を使って OpenCensus / OpenTracing から OpenTelemetry に段階的に移行する](https://zenn.dev/munisystem/articles/a65cc6ca8c2f35)

