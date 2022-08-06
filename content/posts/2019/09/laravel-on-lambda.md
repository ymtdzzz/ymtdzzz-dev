---
title: "LambdaでLaravelを動かす(SAM使用)"
date: 2019-09-07
tags:
  - "AWS"
  - "Lambda"
  - "Laravel"
  - "PHP"
published: True
category: Infrastructure
---
## **Laravel in Lambda**

最近Lambda環境でLaravelを動かす機会がありました。

LaravelはPHPのフレームワークなので、基本的にはPHP用のカスタムランタイムを適用してソースファイルをまるごとアップロードすれば動きます。 

ただ、手動でzipで固めてアップロードして&#8230;というのもなんかあれなので、今回はCloudformationの拡張であるServerless Application Model(SAM)を使用してデプロイまでやってみたいと思います。   

<!--more-->
  
今回はとりあえず動作確認するまでなので、以下の点は**考慮しません**。また別の記事でまとめたいと思います。 

  * 静的リソース(publicディレクトリ配下等)をCloudFrontで配信(CORS対応)
  * ファイルをS3にアップロードする

**前提として、下記を想定しています。** 

  * Composerを導入済
  * AWS CLIを導入済
  * IAMで作成したユーザー情報をaws configureで登録済- 東京リージョンを使用(ap-northeast-1)

## **ローカルでプロジェクトファイル作成**

はじめに、ローカル環境で通常通りプロジェクトを作成して、vendorの生成、dump-autoload等を行います。 

```bash
$ composer create-project --prefer-dist laravel/laravel SampleProject
$ cd SampleProject
$ composer require bref/bref
$ composer install --no-dev
```

次に、Lambdaデプロイのためにソースコードを一部改変します。 

```php
// bootstrap/app.php
$app = new Illuminate\Foundation\Application(
    $_ENV['APP_BASE_PATH'] ?? dirname(__DIR__)
);

// ↓追加する
$app->useStoragePath($_ENV['APP_STORAGE'] ?? $app->storagePath());
```

```bash
# .env
# 追加
VIEW_COMPILED_PATH=/tmp/storage/framework/views
SESSION_DRIVER=array
LOG_CHANNEL=stderr
```

```php
// app/Providers/AppServiceProvider.php
public function boot()
{
  // ↓を追加
  if (! is_dir(config('view.compiled'))) {
      mkdir(config('view.compiled'), 0755, true);
  }
}
```

プロジェクトのソースファイルの準備はこれでOK。 

## **SAMでLambdaにデプロイ**

続いて、SAMを使用してLambdaにデプロイします。 

### **SAMコマンドの導入**

SAMコマンドが叩けない人は、

[AWSのマニュアル][1]を参照してインストールしてください。 導入確認のためにバージョンを確認します。 

```bash
$ sam --version
SAM CLI, version 0.21.0
```

### **SAM用S3バケットを作成**

SAMにデプロイする際、資材一式をS3バケットに配置します。そのため下記のコマンドを実行してバケットを作成しておきます。 

```bash
$ aws s3 mb s3://バケット名 --region リージョンコード
```

もし下記のエラーを吐かれたら、すでに世界中のAWSのどこかで使用されているバケット名なので、ドメイン名などをprefixに追加するなど、ユニークなものになるようにしてください。 

```bash
The requested bucket name is not available.
```

ちなみに上の例ではこのブログのドメイン名を指定しています。 

### **template.yamlの作成**

SAMでのデプロイのために、Lambda関数名やAPI Gatewayのリソース・メソッド名等各種設定をまとめたtemplate.yamlファイルを作成します。 

```bash
$ cd SampleProject
$ touch template.yaml
```

```yaml
AWSTemplateFormatVersion: 2010-09-09
Description: AWSTemplate for SampleProject
Transform: AWS::Serverless-2016-10-31
Resources:
  cfsProduction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub SampleProject
      Description: SampleProject
      Runtime: provided
      Handler: public/index.php
      MemorySize: 3008
      Timeout: 30
      Tracing: Active
      CodeUri: ./
      Layers:
        - !Sub arn:aws:lambda:ap-northeast-1:209497400698:layer:php-73-fpm:7
      Events:
        api:
          Type: Api
          Properties:
            Path: /{proxy+}
            Method: ANY
        api:
          Type: Api
          Properties:
            Path: /
            Method: ANY
```

### **デプロイ実行**

```bash
$ sam package --template-file &lt;templateとなるyamlファイル名（template.yaml等）> --output-template-file serverless-output.yaml --s3-bucket ＜先ほど作成したSAM用バケット名＞

$ sam deploy --template-file serverless-output.yaml --stack-name ＜任意のスタック名＞  --capabilities CAPABILITY_IAM
```

コマンドが成功すると、CloudFormationに新しいスタックが作成され、Lambdaにもデプロイされます。 

API Gatewayのエンドポイントにアクセスすると、Laravelのwelcome画面が表示されます。

![](/images/old/wordpress/laravel.png)

やったぜ。

 [1]: https://docs.aws.amazon.com/ja_jp/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html
