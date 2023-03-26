---
title: NginxでOpenTelemetry（旧バージョンを含む）
date: 2023-03-26
tags:
 - OpenTelemetry
 - Go
 - nginx
published: true
category: Observability
---

NginxでOpenTelemetryを使ってみたかったので色々調べてみました（仕事でも一部Nginxを置いているサーバーがあるというのもあり）。


instrumentationできることはもちろんですが、アクセスログの末尾にtrace idやspan idを渡せれば既存のアクセスログの出力方法はそのままで、DatadogのようなSaaS側でログとトレーシングを紐付けることが可能になるのでよりシームレスに移行することが可能になるかと思います。


見たところ、使えそうなモジュールは２種類ありそうでした。

- [https://github.com/open-telemetry/opentelemetry-cpp-contrib/tree/main/instrumentation/nginx](https://github.com/open-telemetry/opentelemetry-cpp-contrib/tree/main/instrumentation/nginx)
- [https://github.com/open-telemetry/opentelemetry-cpp-contrib/tree/main/instrumentation/otel-webserver-module](https://github.com/open-telemetry/opentelemetry-cpp-contrib/tree/main/instrumentation/otel-webserver-module)

機能部分比較してみましたが、ログ出力などで利用可能な変数やディレクティブの豊富さなどを考えると、前者のnginx instrumentationが良さそうです。


なお、今回の記事で取り上げたサンプル実装のリポジトリはこちらです。


[https://github.com/ymtdzzz/nginx-otel-sample](https://github.com/ymtdzzz/nginx-otel-sample)


# Table of Contents


# 導入方法はざっくり２通り


## 1. nginx: stable or mainline, os: linux or debian（推奨パターン）


nginxはstableかmainlineを使っていて、環境がlinuxかdebianの場合は[Github Actions](https://github.com/open-telemetry/opentelemetry-cpp-contrib/actions/runs/3849659523)に上がっている`.so`ファイルをダウンロードして、nginxで読み込めばOKです。


ただし、現状nginxのstableが`1.22.1`、mainlineが`1.23.3`となっているのと、コンテナ環境だとalpineなんかで運用しているケースも多いと思いますが、その場合はこちらの方法は使えません。


## 2. それ以外の場合　※当記事のスコープ


今回はこちらで見てみようと思います。仕事でも一部サーバーがopenrestyの1.19系なのもあり、古いサーバーで動かせるかどうか見てみようと思いました。


# 前提


## 環境


改めて、環境は下記の通り。


```text
[host]
PRETTY_NAME="Ubuntu 22.04.2 LTS"
NAME="Ubuntu"
VERSION_ID="22.04"
VERSION="22.04.2 LTS (Jammy Jellyfish)"

[container]
image: openresty/openresty:1.19.3.1-2-alpine
proxy: nginx(openresty) v1.19.3.1
backend: Golang v1.20.1
```


## 条件

- edgeは使わない
- ビルド用コンテナを用意し、実際にnginxが動作するコンテナには余計な依存関係を入れたくない

# ビルド用Dockerfile


最終的にこんな感じになりました（ [上がってたissue](https://github.com/open-telemetry/opentelemetry-cpp-contrib/issues/199#issuecomment-1263857801)とほぼ同じです。本当に感謝。 ）


```docker
FROM openresty/openresty:1.19.3.1-2-alpine as builder

RUN apk update \
  && apk add --update \
      alpine-sdk build-base cmake linux-headers libressl-dev pcre-dev zlib-dev \
      curl-dev protobuf-dev c-ares-dev \
      re2-dev

ENV GRPC_VERSION v1.43.2
RUN git clone --shallow-submodules --depth 1 --recurse-submodules -b ${GRPC_VERSION} \
  https://github.com/grpc/grpc \
  && cd grpc \
  && mkdir -p cmake/build \
  && cd cmake/build \
  && cmake \
    -DgRPC_INSTALL=ON \
    -DgRPC_BUILD_TESTS=OFF \
    -DCMAKE_INSTALL_PREFIX=/install \
    -DCMAKE_BUILD_TYPE=Release \
    -DgRPC_BUILD_GRPC_NODE_PLUGIN=OFF \
    -DgRPC_BUILD_GRPC_OBJECTIVE_C_PLUGIN=OFF \
    -DgRPC_BUILD_GRPC_PHP_PLUGIN=OFF \
    -DgRPC_BUILD_GRPC_PHP_PLUGIN=OFF \
    -DgRPC_BUILD_GRPC_PYTHON_PLUGIN=OFF \
    -DgRPC_BUILD_GRPC_RUBY_PLUGIN=OFF \
    ../.. \
  && make -j7 \
    && make install

ENV OPENTELEMETRY_VERSION v1.3.0
RUN git clone --shallow-submodules --depth 1 --recurse-submodules -b ${OPENTELEMETRY_VERSION} \
  https://github.com/open-telemetry/opentelemetry-cpp.git \
  && cd opentelemetry-cpp \
  && mkdir build \
  && cd build \
  && cmake -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=/install \
    -DCMAKE_PREFIX_PATH=/install \
    -DWITH_ZIPKIN=OFF \
    -DWITH_JAEGER=OFF \
    -DWITH_OTLP=ON \
    -DWITH_OTLP_GRPC=ON \
    -DWITH_OTLP_HTTP=OFF \
    -DBUILD_TESTING=OFF \
    -DWITH_EXAMPLES=OFF \
    -DWITH_ABSEIL=ON \
    -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
    .. \
  && make -j7 \
  && make install

RUN git clone https://github.com/open-telemetry/opentelemetry-cpp-contrib.git \
  && cd opentelemetry-cpp-contrib/instrumentation/nginx \
  && mkdir build \
  && cd build \
  && cmake -DCMAKE_BUILD_TYPE=Release \
    -DNGINX_BIN=/usr/local/openresty/nginx/sbin/nginx \
    -DCMAKE_PREFIX_PATH=/install \
    -DCMAKE_INSTALL_PREFIX=/usr/lib/nginx/modules \
    .. \
  && make -j7 \
  && make install

FROM openresty/openresty:1.19.3.1-2-alpine

RUN apk update \
  && apk add --no-cache libstdc++

COPY --from=builder /usr/lib/nginx/modules/otel_ngx_module.so /usr/lib/nginx/modules/
  
ADD ./otel-nginx.toml /conf/otel-nginx.toml
ADD ./nginx.conf /etc/nginx/conf.d/default.conf
ADD ./nginx-base.conf /usr/local/openresty/nginx/conf/nginx.conf
```


やってることとしては、依存しているgrpc, opentelemetry-cppをソースからビルドし、最後にnginx moduleもビルドして出来上がったモジュールを最終成果物のimageに読み込んで焼き付けています。


## ぶち当たった問題


ソースからビルドすれば良いのはわかっていたのですが、最終的に動くまで結構ハマったのでまとめておきます。


### nginxの動的モジュールのバージョン問題


nginxのバイナリと、ビルドしたモジュールのバージョンが一致していないといけないので、ビルドは同じコンテナイメージで実行する必要がありました。


まあ、imageを合わせれば良いのでここはそんなに問題にはならないかなと思います（自分のnginx力が足りなくてググったくらい）。


### opentelemetry-cpp-devがedge


[https://pkgs.alpinelinux.org/packages?name=opentelemetry-cpp-*&branch=edge&repo=&arch=&maintainer=](https://pkgs.alpinelinux.org/packages?name=opentelemetry-cpp-*&branch=edge&repo=&arch=&maintainer=)


既存リポジトリと併用すると他のパッケージも巻き込まれて壊れる可能性があるのでパッケージ管理ツールでさくっと入れるのは諦めました。


### cmake関連のエラー


<u>**nlohmann_json::nlohmann_json**</u>


```text
CMake Error at /usr/lib/cmake/opentelemetry-cpp/opentelemetry-cpp-target.cmake:179 (set_target_properties):
  The link interface of target "opentelemetry-cpp::otlp_http_client"
  contains:

    nlohmann_json::nlohmann_json
```


edgeの件はあったものの、とりあえずドキュメント通り`apk add opentelemetry-cpp-dev`後にビルドしたら出てきたエラー。


<u>**nginx起動時のundefined symbol系**</u>


最終的にgrpc, opentelemetry-cpp, nginx instrumentationをソースからビルドするときに遭遇した。


下記のようなもの。


```text
_znst7__cxx1118basic_stringstreamicst11char_traitsicesaiceec1ev symbol not found
ZN4grpc6Status2OKE: symbol not found
```


上のはたしかzlibstdc++のバージョンがビルド環境と使用環境で異なったのが原因で、下のは結局よくわからず（grpc関連だろうなとは思いつつ）、後述のDockerfileを作り上げたら解消していた。


# 他ファイル


[リポジトリ](https://github.com/ymtdzzz/nginx-otel-sample)を見ていただければと思いますが、一部抜粋します。


## nginx


```text
...
load_module /usr/lib/nginx/modules/otel_ngx_module.so;
...
http {
		...

    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for" '
                      'trace_id: "$opentelemetry_trace_id" span_id: "$opentelemetry_span_id"';

    access_log  /usr/local/openresty/nginx/logs/access.log  main;
```


細かいディレクティブは[公式ドキュメント](https://github.com/open-telemetry/opentelemetry-cpp-contrib/tree/main/instrumentation/nginx)を参照いただくとして、ここではデフォルトで有効になっているinstrumentationの他、アクセスログにtrace idとspan idを入れるために`$opentelemetry_trace_id`と`$opentelemetry_span_id`を利用利用しています。


## golang


アプリ側もinstrumentationしています（otelhttpによるauto instrumentation）。


```go
	mux := http.NewServeMux()
	mux.HandleFunc("/hello", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})
	h := otelhttp.NewHandler(mux, "server",
		otelhttp.WithMessageEvents(otelhttp.ReadEvents, otelhttp.WriteEvents),
	)
	srv := &http.Server{
		Addr:    ":8080",
		Handler: h,
	}
```


# 動作確認


最後に、実際に動かしてみます（`docker compose up`）。


[http://localhost:8081/hello](http://localhost:8081/hello) に何度かアクセス後、jaeger UIを確認してみます（ [http://localhost:16686](http://localhost:16686/) ）。


![ee89fd86-5ac5-4b54-a157-7f4b7b8b857a.png](../../../../gridsome-theme/src/assets/images/notion/ee89fd86-5ac5-4b54-a157-7f4b7b8b857a.png)


`nginx-proxy`がnginx側で出力されたspanで、`server`がgoのアプリケーション側で生成されたspanです。とりあえずinstrumentationとしてはちゃんと動いてそうです。


続いて、アクセスログを確認してみます（ `docker compose logs nginx` ）


```text
172.22.0.1 - - [26/Mar/2023:08:59:42 +0000] "GET /hello HTTP/1.1" 200 0 "-" "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36" "-" trace_id: "264701e54887f0184c59dff28dbce34b" span_id: "9b35c53da88fab20"
```


きちんとtrace idとspan idが取れてますね。


# 最後に


意外と苦労しましたが、任意のnginxバージョンでopentelemetry instrumentationが利用できそうです。また、アクセスログにもtrace id, span idを埋め込むことで、Datadogのようなツールと連携しやすくなりました。


パフォーマンス面についてはさらなる検証が必要ですが、ミドルウェアのinstrumentationも可能だということがわかり、個人的には学びが多かったです。


誰かの参考になれば幸いです。


# 参考

- [https://github.com/open-telemetry/opentelemetry-cpp-contrib/tree/main/instrumentation/nginx](https://github.com/open-telemetry/opentelemetry-cpp-contrib/tree/main/instrumentation/nginx)
- [https://github.com/open-telemetry/opentelemetry-cpp-contrib/issues/199](https://github.com/open-telemetry/opentelemetry-cpp-contrib/issues/199)
