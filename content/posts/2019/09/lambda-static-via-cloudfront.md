---
title: "【CORS対応】Lambdaで動くLaravelの静的ファイルをCloudFrontで配信する"
date: 2019-09-17
tags:
  - "AWS"
  - "CDN"
  - "CloudFront"
  - "CORS"
  - "Lambda"
  - "Laravel"
published: True
category: Infrastructure
---
## **静的ファイルをキャッシュしたい**

前回の記事ではLambda上にLaravelを構築しました。 

とりあえず動くは動くんですが、Lambda上で全てのファイルをいちいち読み込んでいるので、容量が大きいファイルをやりとりするサービスではパフォーマンス面で不安が残ります。   

そのため、今回の記事では静的ファイル（publicフォルダ配下）をS3に配置し、Cloudfrontで高速に配信できるようにしたいと思います。また、キャッシュサーバから受信したCSS等から別サーバのリソースを読み込むことを考慮し、CORS設定も行っていきたいと思います。 

<!--more-->

## **静的リソースの作成＋適用**

まず、resources/views/welcome.blade.phpを下記の通り編集します。

```html
<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" href="{{ Config::get('app.asset_url') }}/css/style.css">

        <title>Laravel&lt;/title>
    </head>
    <body>
        <div class="test-box">
            CSSテストです。
        </div>
    </body>
</html>

<link rel="stylesheet" href="{{ Config::get('app.asset_url') }}/css/style.css">
```

laravelのconfig設定からCDNのドメイン名を取得して読み込むCSSを指定してあります。Laravelソースファイル側の設定方法については後述します。 
  
続いて、CSSの読み込み先であるCSSファイルを作成します。動作確認なので適当に。 

```css
@charset "utf-8";

.test-box {
  border: 2px solid red;
  background-image: url('../images/background.jpg');
  padding: 30px;
}
```

画像ファイルは

<span class="marker">public/images/background.jpg</span>に準備しておきます。 これで一旦publicフォルダの準備はOK。 

## **S3に静的リソースを配置**

まずは静的リソース配置用バケットを作成します。 

```bash
$ aws s3 s3://バケット名 --region リージョンコード
```

続いて、プロジェクトフォルダ内のpublicリソースをアップロードします。 

```bash
$ cd /path/to/your/project/path
$ aws s3 cp public s3://バケット名/ --recursive --acl public-read
```

## **CloudFrontの設定**

CloudFrontの設定を行います。 今回はGUIでやります。 

  * CloudFrontのTOPから「Create&nbsp;Distribution」を選択
  * Webの方の「Get&nbsp;Started」を選択
  * Distribution設定を行う
  
入力フォームがずら〜っと出てきますが、デフォルトから変更する部分は一旦下記項目だけ。（Origin Pathは、今回はpublic配下をまるごとアップロードするだけなので未指定でOK）

入力後、「Create Distribution」を押下します。作成完了後も、Statusはしばらく「In&nbsp;Progress」だと思うので、先に別の作業をしちゃいましょう。 

あ、その前に、Distributionの詳細画面から「Domain&nbsp;Name」をメモっておいてください。カスタムドメインを設定しないと「<ランダムな文字列>.cloudfront.net」の形式になっていると思います。 

## **Lambdaのソース修正**

ドメイン名を確認したところで、今度はLambdaにデプロイしたLaravelソースコードの修正を行います。 
  
まず、.envファイルに下記のコードを追加します。今回はしませんが、環境ごとにSSL対応を切り替えたりするのも見越してSECURE環境変数も追加しています。   

```bash
ASSET_DOMAIN=<cloudfrontのドメイン名>
SECURE=true
```

config/app.phpも編集します。   

```php
    'url' => env('APP_URL', 'http://localhost'),

    // 以下追加
    'asset_url' => 'http' . (env('SECURE') ? 's' : '') . '://' . env('ASSET_DOMAIN'),
    'asset_domain' => env('ASSET_DOMAIN', null),
```
    
以上を設定し終わると、

`Config::get('app.asset_url')`の結果としてCDNのドメイン名が返ってきますので、これでCDNの静的リソースを読み込んでやろうという流れです。   
  
編集が完了したら、前回の記事と同様にしてSAMでLambdaにデプロイします。   

まだCSSは反映されませんので注意。   

## **S3の公開設定とCORS対応**

S3のバケットポリシーに以下のJSONを追加します（xxxは任意のバケット名）。 

```json
{
    "Version":"2012-10-17",
    "Statement":
    [
        {
            "Sid":"PublicAccessPermission",
                "Effect":"Allow",
            "Principal": "*",
            "Action":"s3:GetObject",
            "Resource":"arn:aws:s3:::xxxxxxxxxxx/*"
        }
    ]
}
```

今回のサンプルではここまでの設定でも動きますが、今後のためにCORS対応もしておきます。 
  
S3の「CORSの設定」に設定を行います。   

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CORSConfiguration xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
  <CORSRule>
    <AllowedOrigin>*&lt;/AllowedOrigin>
    <AllowedMethod>GET&lt;/AllowedMethod>
    <MaxAgeSeconds>3000&lt;/MaxAgeSeconds>
    <AllowedHeader>*&lt;/AllowedHeader>
  </CORSRule>
</CORSConfiguration>
```

CloudFrontの

`Behaviors`->`Edit`にて下記設定を行います。   

  * <span class="marker">Cache&nbsp;Based&nbsp;on&nbsp;Selected&nbsp;Request&nbsp;Headers</span>を<span class="marker">Whitelist</span>に変更
  * <span class="marker">Whitelist&nbsp;Headers</span>に<span class="marker">Origin</span>を追加
  
これでLambdaのAPI&nbsp;Gatewayのendpointに接続すると･･･ 

![](../../../../gridsome-theme/src/assets/images/old/wordpress/static-via-cdn.png)

現場からは以上です。
