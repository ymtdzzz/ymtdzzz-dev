---
title: コントリビューター視点でのOpenTelemetry Demoの使い道を考える
date: 2022-11-28
tags:
 - OpenTelemetry
 - Go
 - Docker
 - OSS
published: true
category: Observability
---

こんにちは、[@ymtdzzz](https://twitter.com/ymtdzzz)です。


この記事は[OpenTelemetry Advent Calendar 2022](https://qiita.com/advent-calendar/2022/opentelemetry)の4日目の記事です。3日目は[@munisystem](https://twitter.com/munisystem)さんの「[bridge を使って OpenCensus / OpenTracing から OpenTelemetry に段階的に移行する](https://zenn.dev/munisystem/articles/a65cc6ca8c2f35)」でした。


違うネタでもう少し先に書かせていただく予定でしたが、ネタがあったのでせっかくなので滑り込みで書かせていただきます。


# はじめに


2022年10月24日に、opentelemetry-demoがGAを迎えました。


[https://opentelemetry.io/blog/2022/announcing-opentelemetry-demo-release/](https://opentelemetry.io/blog/2022/announcing-opentelemetry-demo-release/)


このデモアプリはECサイトを模した作りになっており、それぞれ異なる言語で実装されたマイクロサービスで構成されています。そして、それぞれがOpenTelemetryの機能を最大限活かして実装されており、OpenTelemetryの機能や実装を確認するのに非常に参考になるリポジトリになっています。


[リポジトリのREADME](https://github.com/open-telemetry/opentelemetry-demo#welcome-to-the-opentelemetry-astronomy-shop-demo)によると、デモアプリの目的は下記の3点みたいです。

- Provide a realistic example of a distributed system that can be used to demonstrate OpenTelemetry instrumentation and observability.
- Build a base for vendors, tooling authors, and others to extend and demonstrate their OpenTelemetry integrations.
- Create a living example for OpenTelemetry contributors to use for testing new versions of the API, SDK, and other components or enhancements.

勝手に翻訳）

- OpenTelemetryの計装と可観測性を実証するのに使用できる、分散システムの現実的な例を提供する
- ベンダーやツール作成者、その他のユーザーがOpenTelemetry統合を拡張したり実証したりするための基盤を構築する
- OpenTelemetryのコントリビューターがAPI, SDKやその他のコンポーネントや新機能をテストするために使える生きた例を作成する

実際のプロダクトに導入するためのリファレンス実装を提供するのに加え、OpenTelemetry関連のリポジトリへの貢献する際の検証環境としても使えそうです。


私もちょこちょこPR送っているので、今回は後者に着目して色々試してみたいと思います。


# Demoリポジトリ概要


初めにどこにどんな情報があるかをまとめておきます。


## サービス一覧と実装言語


サービスと実装言語については下記のドキュメントに記載があります。


[https://github.com/open-telemetry/opentelemetry-demo/blob/main/docs/service_table.md](https://github.com/open-telemetry/opentelemetry-demo/blob/main/docs/service_table.md)


## 実装ステータス


DemoでどこまでOpenTelemetryの機能をカバーできているかについてはこちら。

- [Tracing](https://github.com/open-telemetry/opentelemetry-demo/blob/main/docs/trace_service_features.md)
- [Metrics](https://github.com/open-telemetry/opentelemetry-demo/blob/main/docs/metric_service_features.md)
- Logging
	- APIとSDKはまだspecでdraftのステータスなのでまだっぽい。現状LogRecordはLoggingではなくTrace Eventで記録しているようです。

## Manual Span Attributes


サービス固有の、手動でSpanに追加しているAttributesの一覧。


[https://github.com/open-telemetry/opentelemetry-demo/blob/main/docs/manual_span_attributes.md](https://github.com/open-telemetry/opentelemetry-demo/blob/main/docs/manual_span_attributes.md)


## デプロイ方法


デプロイ方法はDockerとKubernetesそれぞれ下記のドキュメントにまとまっています。

- [Docker](https://github.com/open-telemetry/opentelemetry-demo/blob/main/docs/docker_deployment.md)
- [Kubernetes](https://github.com/open-telemetry/opentelemetry-demo/blob/main/docs/kubernetes_deployment.md)

# OpenTelemetryの検証環境として使う


OpenTelemetryそれ自体の検証環境として使うための条件はこんな感じでしょうか。

- 個別のリポジトリ（言語別のinstrumentation libraryやcollector、contribなど）について、ローカルで変更してビルドしたバージョンをdemoに組み込めること
- exporterやバックエンドなどを自由に切り替えできること

それぞれ機能追加やバグ修正で動作確認するためには必要で、また、バグの再現確認でも必要になってきそうです。


いくつかリポジトリを取り上げてdemoへの組み込み方法を確認してみます。


## opentelemetry-collector-contrib


例えばこのissue


[https://github.com/open-telemetry/opentelemetry-collector-contrib/issues/16538](https://github.com/open-telemetry/opentelemetry-collector-contrib/issues/16538)


prometheus receiverの設定が空の場合にpanicするというissueですが、configに設定してあげるだけで再現確認ができそうです。


せっかくなので手元のソースコードでビルドしたotelcolを組み込んで動作確認してみます。


まずはdemo側の設定にprometheus receiverを追加し、metrics pipelineに追加します。


[https://github.com/open-telemetry/opentelemetry-demo/blob/15d8956f91bb1a8cb76a5443aa6369995cdcaa2d/src/otelcollector/otelcol-config.yml#L1-L9](https://github.com/open-telemetry/opentelemetry-demo/blob/15d8956f91bb1a8cb76a5443aa6369995cdcaa2d/src/otelcollector/otelcol-config.yml#L1-L9)


```yaml
receivers:
  prometheus: # add prometheus
  otlp:
    protocols:
      grpc:
...
service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [spanmetrics, batch]
      exporters: [logging, otlp]
    metrics:
      receivers: [otlp, prometheus] # add prometheus
      processors: [batch]
      exporters: [prometheus, logging]
```


続いて、[opentelemetry-collector-conrib](https://github.com/open-telemetry/opentelemetry-collector-contrib)のソースをチェックアウトし、手元でビルドします。


```shell
# cloneしたディレクトリ
$ make docker-otelcontribcol
# ビルドしたimageを確認
$ docker images | grep otelcontribcol
otelcontribcol                         latest                         12e57e115ec1   5 minutes ago   270MB
```


demoのリポジトリに戻り、`docker-compose.yaml`のotelcol serviceのイメージを手元のimageに変更します。


[https://github.com/open-telemetry/opentelemetry-demo/blob/15d8956f91bb1a8cb76a5443aa6369995cdcaa2d/docker-compose.yml#L489](https://github.com/open-telemetry/opentelemetry-demo/blob/15d8956f91bb1a8cb76a5443aa6369995cdcaa2d/docker-compose.yml#L489)


```yaml
otelcol:
    image: otelcontribcol:latest
```


この状態で起動（`docker compose up —no-build -d & docker compose logs otelcol`）すると、確かに再現しました。


```shell
otel-col  | 2022-11-30T13:38:45.205Z    info    pipelines/pipelines.go:102      Receiver is starting... {"kind": "receiver", "name": "prometheus", "pipeline": "metrics"}
otel-col  | panic: runtime error: invalid memory address or nil pointer dereference
otel-col  | [signal SIGSEGV: segmentation violation code=0x1 addr=0x0 pc=0x4766d4d]
otel-col  |
otel-col  | goroutine 1 [running]:
otel-col  | github.com/open-telemetry/opentelemetry-collector-contrib/receiver/prometheusreceiver.gcInterval(...)
```


エラー内容的に、receiverのstart時に通る`gcInterval()`のcfgがnilの状態を考慮できていない可能性が高そうなので、試しにnilチェックを入れてみます


[https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/receiver/prometheusreceiver/metrics_receiver.go](https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/receiver/prometheusreceiver/metrics_receiver.go)


```go
func gcInterval(cfg *config.Config) time.Duration {
	gcInterval := defaultGCInterval
	if cfg == nil { // 追加
		return gcInterval
	}
	if time.Duration(cfg.GlobalConfig.ScrapeInterval)+gcIntervalDelta > gcInterval {
		gcInterval = time.Duration(cfg.GlobalConfig.ScrapeInterval) + gcIntervalDelta
```


この対応を入れて再度imageをビルドしてdemoを再起動すると、該当箇所のエラーは解消されましたが、今度は似たような別の場所でエラーが発生しました。


対応方針についてはissueやPRで議論する必要がありそうですが、こんな調子でローカルで開発できそうです。


ということでPR上げておきました（default configを使用する方針に変更）


[https://github.com/open-telemetry/opentelemetry-collector-contrib/pull/16584](https://github.com/open-telemetry/opentelemetry-collector-contrib/pull/16584)


今回のissueは再現方法が非常にシンプルなので元のリポジトリでシングルバイナリ＋configで確かめられそうですが、色々なバックエンドやpipelineを組み合わせた実践的な構成で発生したエラーについては、demoの環境を使った方が検証しやすいと思います。


## opentelemetry-go


続いて、instrumentation libraryを見てみます。今回はgolangで。よさげなissueを探す時間がなかったので組み込み方法だけ確認してみます。


基本的にinstrumentation libraryについては言語毎のパッケージ管理方法に拠ります。


demoの中でgolangで実装されているサービスは`productcatalogservice`と`checkoutservice`なので、今回は`checkoutservice`で使っているSDKをローカルの実装と置き換えてみようと思います。


<u>**opentelemetry-demoでの作業**</u>


demoの`go.mod`で、該当パッケージをローカルにreplaceする設定を追加します。


```shell
cd src/checkoutservice
go mod edit -replace go.opentelemetry.io/otel/sdk@v1.10.0=./opentelemetry-go/sdk
```


demoのdocker imageをビルドする際には、外部ディレクトリにcloneしたopentelemetry-goを参照できない（build contextの親ディレクトリを参照できない）のでopentelemetry-go側でbase imageを作ってあげる必要があります。


<u>**opentelemetry-goでの作業**</u>


opentelemetry-goのリポジトリ直下に下記のような`Dockerfile`を作成します（imageやworkdirはdemoの該当サービスのDockerfileからコピペでOK）。


```docker
FROM golang:1.19.2-alpine AS builder

WORKDIR /usr/src/app/

COPY ./ ./opentelemetry-go
```


これでベースイメージのworkdir直下にローカルのopentelemetry-goのソースが配置されるので、まずはこれをビルドします。


```shell
docker build -t opentelemetry-go-base:latest .
```


<u>**opentelemetry-demoでの作業**</u>


`checkoutservice`の`Dockerfile`を一部変更し、先程作成したベースイメージからビルドするように変更します。また、`go mod download`を`go mod tidy`に変更して、依存パッケージの解決をするようにしておきます。


[https://github.com/open-telemetry/opentelemetry-demo/blob/main/src/checkoutservice/Dockerfile](https://github.com/open-telemetry/opentelemetry-demo/blob/main/src/checkoutservice/Dockerfile)


```docker
#...

# FROM golang:1.19.2-alpine AS builder
# 先程作成したベースイメージを指定
FROM opentelemetry-go-base:latest AS builder
RUN apk add build-base protobuf-dev protoc
WORKDIR /usr/src/app/

#...
# RUN go mod download
RUN go mod tidy
```


最後に、imageをビルドしてdemoを起動します。


```shell
docker compose build checkoutservice
docker compose up --no-build -d
# ログを確認して、ローカルの実装が動いていることを確認
docker ps | grep checkout
# e3a78a7adcb9   ghcr.io/open-telemetry/demo:v1.1.0-checkoutservice ...
docker logs e3a78a7adcb9 | grep hello
# hello from local!
```


手元のopentelemetry-goのソースでdemoが動いています。これで検証や開発に使うことができるようになりました。


# 終わりに


今回は、私のように気軽にOpenTelemetryにコントリビュートしてみたい人向けにopentelemetry-demoを活用してみる方法について見てみました。


次回は[@Hidekazu-Karino](https://qiita.com/Hidekazu-Karino)さんです！

