---
title: "Lambciとimg2lambdaとserverlessでLambdaのデプロイフローを構築する"
date: 2020-09-02
tags:
  - "AWS"
  - "Lambda"
  - "lambci"
  - "img2lambda"
  - "PHP"
  - "CustomRuntime"
  - "serverless"
published: True
category: Infrastructure
---

## Lambdaのローカル環境 {#lambdaのローカル環境}

これまでLambdaを構築する際には、ソースコードを決め打ちで書いてzipで上げたり、コンソール上のエディタでポチポチ開発していたりしてました。

PythonとかNodejsとかなら、それでも簡単なAPIくらいなら作れるのですが、ちょっと複雑なことになったり、PHPみたいにCustom Runtimeを使いたい場合とかは、何度もデプロイし直してトライアンドエラーするのは効率が悪いです。

やっぱり、他のソースと同じようにローカルでガリガリ書いて、コマンドで自動デプロイができた方が良いので色々探したところ、Lambciとimg2lambda（あとserverless）を使ったフローが良さそうだったので紹介します。

<!--more-->


## lambciとimg2lambda {#lambciとimg2lambda}

はじめに、各ツールの概要を軽く説明します。


### lambci/lambda {#lambci-lambda}

[lambci/lambda](https://hub.docker.com/r/lambci/lambda/) は、Lambdaの環境に非常に近いDockerイメージです。PythonのようなLambdaでデフォルトでサポートしている言語であれば、このイメージをPullしてファイルを配置するだけでLambdaのローカル開発環境がサクッと作れちゃいます。

PHPの場合はCustom Runtimeを作成すれば問題無く動作します（今回の記事で解説）。


### img2lambda {#img2lambda}

[AWS Lambda Container Image Converter(略してimg2lambda)](https://github.com/awslabs/aws-lambda-container-image-converter) は、Dockerコンテナ上のソースコードをLambdaにデプロイ可能なzipファイルに固めてくれるツールです。

配置するコードは下記のルールに従います。

> -   /var/task : Lambdaのソースコード本体
> -   /opt : Lambdaレイヤー

よって、 `/opt` 配下にPHPを動かすためのバイナリとかライブラリ系を配置すれば、Custom Runtimeであってもきちんと固めてくれます。


### Serverless Framework {#serverless-framework}

おなじみの [serverless framework](https://www.serverless.com/) ですが、これは、作成したyamlテンプレートの通りに自動デプロイしてくれるツールです。構成情報をコード化して管理する　という面ではCloudFormationと同じですが、もっと手軽に記述することができます（serverlessがCloudFormationに変換してくれる）。

今回は、img2lambdaで固めたzipとテンプレートファイルをインプットにして、コマンド一発でデプロイするのに使用します。


## 全体像 {#全体像}

流れを図式化すると、下記のような感じです。

![](../../../../gridsome-theme/src/assets/images/old/ox-hugo/20200901_210418.png)

ローカルで開発したイメージをそのままLambdaにデプロイできるので、スムーズにLambdaの開発を行うことができます。


## 実際に作ってみる {#実際に作ってみる}

今回は、カスタムランタイムを使いたいのでPHPでやってみたいと思います。


### lambciによるローカル開発環境のセットアップ {#lambciによるローカル開発環境のセットアップ}

まずは適当にディレクトリを作ってもらって、Dockerfileを作成します。といっても、基本的なところはimg2lambdaのexampleとほぼ同じです。

```dockerfile
#+CAPTION: Dockerfile
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

####### PHP custom runtime #######
####### Install and compile everything #######
# Same AL version as Lambda execution environment AMI
FROM amazonlinux:2018.03.0.20190514 as builder

# Set desired PHP Version
ARG php_version="7.3.6"

# Lock to 2018.03 release (same as Lambda) and install compilation dependencies
RUN sed -i 's;^releasever.*;releasever=2018.03;;' /etc/yum.conf && \
    yum clean all && \
    yum install -y autoconf \
                bison \
                bzip2-devel \
                gcc \
                gcc-c++ \
                git \
                gzip \
                libcurl-devel \
                libxml2-devel \
                make \
                openssl-devel \
                tar \
                unzip \
                zip

# Download the PHP source, compile, and install both PHP and Composer
RUN curl -sL https://github.com/php/php-src/archive/php-${php_version}.tar.gz | tar -xvz && \
    cd php-src-php-${php_version} && \
    ./buildconf --force && \
    ./configure --prefix=/opt/php-7-bin/ --with-openssl --with-curl --with-zlib --without-pear --enable-bcmath --with-bz2 --enable-mbstring --with-mysqli && \
    make -j 5 && \
    make install && \
    /opt/php-7-bin/bin/php -v && \
    curl -sS https://getcomposer.org/installer | /opt/php-7-bin/bin/php -- --install-dir=/opt/php-7-bin/bin/ --filename=composer

# Prepare runtime files
RUN mkdir -p /lambda-php-runtime/bin && \
    cp /opt/php-7-bin/bin/php /lambda-php-runtime/bin/php

COPY runtime/bootstrap /lambda-php-runtime/
RUN chmod 0555 /lambda-php-runtime/bootstrap

RUN /opt/php-7-bin/bin/php /opt/php-7-bin/bin/composer config -g repos.packagist composer https://packagist.jp
RUN /opt/php-7-bin/bin/php /opt/php-7-bin/bin/composer config -g secure-http false

# Install Guzzle, prepare vendor files
RUN mkdir /lambda-php-vendor && \
    cd /lambda-php-vendor && \
    /opt/php-7-bin/bin/php /opt/php-7-bin/bin/composer require guzzlehttp/guzzle && \
    /opt/php-7-bin/bin/php /opt/php-7-bin/bin/composer require aws/aws-sdk-php

###### Create runtime image ######

FROM lambci/lambda:provided as runtime

# Layer 1
COPY --from=builder /lambda-php-runtime /opt/

# Layer 2
COPY --from=builder /lambda-php-vendor/vendor /opt/vendor

###### Create function image ######

FROM runtime as function

COPY function/hello /var/task/src/
```

続いて、docker-compose.yamlを作成します。コンテナ一つでも楽なのでいつもdocker-compose使ってます。

```yaml
#+CAPTION: docker-compose.yaml
version: '3'
services:
  lambda_hello:
    build: .
    tty: true
    working_dir: /var/task/src
    ports:
      - 9001:9001
    volumes:
      - ./function/hello:/var/task/src:delegated
    environment:
      DOCKER_LAMBDA_WATCH: 1
      DOCKER_LAMBDA_STAY_OPEN: 1
      DOCKER_LAMBDA_API_PORT: 9001
      TEST_ENV_VAR: "hello world!"
    command: hello
```

function/hello/hello.phpを作成して、Lambda関数本体を作成します。環境変数からデータを取得して返却するだけの処理です。

```php
#+CAPTION: function/hello/hello.php
<?php

function hello($data)
{
    $data = json_decode($data['body'], true);
    $text = getenv('TEST_ENV_VAR');
    $param = (isset($data['param'])) ? $data['param'] : '山田 太郎';
    $response = [
        'statusCode' => 200,
        'body' => $text . ' ' . $param . 'さん',
    ];
    return $response;
}
```

次に、runtime/bootstrapを作成します。これは、Lambdaで取得したリクエストを取得して、パラメータをhandler（今回はhello.php）に渡し、返却されたデータをレスポンスとして返却しています。

http通信周りはGuzzleを使用しているので、コード自体は44step程度しかないです。

```php
#+CAPTION: runtime/bootstrap
#!/opt/bin/php
<?php

// Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

// This invokes Composer's autoloader so that we'll be able to use Guzzle and any other 3rd party libraries we need.
require __DIR__ . '/vendor/autoload.php';

function getNextRequest()
{
    $client = new \GuzzleHttp\Client();
    $response = $client->get('http://' . $_ENV['AWS_LAMBDA_RUNTIME_API'] . '/2018-06-01/runtime/invocation/next');

    return [
      'invocationId' => $response->getHeader('Lambda-Runtime-Aws-Request-Id')[0],
      'payload' => json_decode((string) $response->getBody(), true)
    ];
}

function sendResponse($invocationId, $response)
{
    $client = new \GuzzleHttp\Client();
    $client->post(
      'http://' . $_ENV['AWS_LAMBDA_RUNTIME_API'] . '/2018-06-01/runtime/invocation/' . $invocationId . '/response',
      ['body' => json_encode($response)]
    );
}

// This is the request processing loop. Barring unrecoverable failure, this loop runs until the environment shuts down.
do {
    // Ask the runtime API for a request to handle.
    $request = getNextRequest();

    // Obtain the function name from the _HANDLER environment variable and ensure the function's code is available.
    $handlerFunction = array_slice(explode('.', $_ENV['_HANDLER']), -1)[0];
    require_once $_ENV['LAMBDA_TASK_ROOT'] . '/src/' . $handlerFunction . '.php';

    // Execute the desired function and obtain the response.
    $response = $handlerFunction($request['payload']);

    // Submit the response back to the runtime API.
    sendResponse($request['invocationId'], $response);
} while (true);
```

さて、これでdocker-composeを起動してみます。

```bash
#+CAPTION: docker-compose起動
$ docker-compose up -d
```

PHPをソースからビルドするので初回起動のイメージビルド時は若干時間がかかります。

コンテナが起動したら、軽く動作確認します。

```bash
#+caption: 動作確認
$ curl -d '{}' http://localhost:9001/2015-03-31/functions/hello/invocations
{"statusCode":200,"body":"hello world! \u5c71\u7530 \u592a\u90ce\u3055\u3093"}
```

ちゃんと期待通り動作してますね。ちょっと補足ですが、デプロイ先の環境はAPI Gatewayのプロキシ統合を使用するので、レスポンスパターンはきちんと合わせます。

ローカルだとresponseCodeを400とかに設定してもAPIを叩くと200になってしまいますが、デプロイされるときちんと400になります（このあたりの差分をローカルでもきちんと吸収したいけどイマイチ解決策が見つからず・・・）。

また、リクエストパラメータについても、API Gatewayを通るとJSONオブジェクトのbodyパラメータにテキストでエンドユーザが送ったパラメータが格納されるので注意です。


### img2lambdaでデプロイパッケージを作成する {#img2lambdaでデプロイパッケージを作成する}

さて、ここまでくると下記のようなディレクトリ構成になっているかと思います。

![](../../../../gridsome-theme/src/assets/images/old/ox-hugo/overview.svg)

インストールは、[GithubのReleaseページ](https://github.com/awslabs/aws-lambda-container-image-converter/releases) から、それぞれのプラットフォーム用のバイナリをダウンロードしてパスが通ってるところに配置するだけです。

```bash
#+caption: img2lambdaのインストール確認
$ img2lambda --version
img2lambda version 1.2.4 (1d7760a)
```

これでローカルのDockerコンテナをデプロイパッケージに固める準備ができたので、下記のコマンドをプロジェクトルートディレクトリで実行します。

```bash
$ img2lambda -i lambci_lambda_hello:latest -r ap-northeast-1 -o ./output
2020/09/02 08:58:29 Parsing the image docker-daemon:lambci_lambda_hello:latest
2020/09/02 08:58:58 Image docker-daemon:lambci_lambda_hello:latest has 5 layers
...
2020/09/02 09:00:07 Lambda layer ARNs (2 total) are written to output/layers.json and output/layers.yaml
```


### serverlessで自動デプロイする {#serverlessで自動デプロイする}

デプロイパッケージの準備ができたので、serverlessで自動デプロイします。

deploy/serverless.ymlを作成し、下記のように記述します。

```yaml
service: Lambda

provider:
  name: aws
  runtime: provided
  region: ap-northeast-1

package:
  individually: true

functions:
  LambciHello:
    handler: hello
    package:
      artifact: ../output/function.zip
    layers:
      ${file(../output/layers.json)}
    events:
      - http:
          path: /hello
          method: post
    environment:
      TEST_ENV_VAR: "hello from lambda!"
```

それではデプロイしてみます（ `aws configure` とかはやっといてね）。

```bash
$ cd deploy
$ sls deploy
```

正常に完了すると、きちんとLambdaとAPI Gatewayが作成されていることがわかります。

![](../../../../gridsome-theme/src/assets/images/old/ox-hugo/20200902_091337.png)

実際にPOSTしてみると、たしかに期待通りのレスポンスが返ってきています。

```bash
$ curl -d '{}' https://*********.execute-api.ap-northeast-1.amazonaws.com/dev/hello
hello from lambda! 山田 太郎さん

$ curl -d '{"param": "田中 次郎"}' https://*********.execute-api.ap-northeast-1.amazonaws.com/dev/hello
hello from lambda! 田中 次郎さん
```


### おわりに {#おわりに}

今の所上記のようなフローで開発が進めていますが、ローカルでAPI Gatewayのプロキシ統合がシミュレートできない点についてはもう少し改善の余地があるかなーと思います。

現状、環境によって下記のようにエスケープしないといけないので・・・。


#### ローカル {#ローカル}

```json
{
    "body": "{\r\n\"param\": \"aiueo\"\r\n}"
}
```


#### Lambda {#lambda}

```json
{
    "param": "aiueo"
}
```

まあ、そこを除けば良いフローかと思います。

そのうち、SAMのローカル環境とかも試してみたい。
