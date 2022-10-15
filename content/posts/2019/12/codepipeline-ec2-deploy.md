---
title: "【AWS】CodePipelineでEC2への最低限の自動デプロイ環境を整備する"
date: 2019-12-30
tags:
  - "AWS"
  - "CodeBuild"
  - "CodeCommit"
  - "CodeDeploy"
  - "CodePipeline"
published: True
category: DevOps
---
## CodePipelineを用いたEC2への自動デプロイ

AWSには様々なデプロイ手法が存在する。CodeDeployを使用すればEC2,Lambda,Fargateに自動デプロイ（もちろん手動も）できる他、CodeBuildを利用すればS3へのアップロード、CloudFrontのキャッシュ削除（Invalidation）も勝手にやってくれたり。

CloudFormationを使用してLambdaにデプロイする方法についても今度詳しく記事を書きたいと思っているが、今回は前回の記事でも触れたEC2への自動deployについて紹介する。 

<!--more-->

### 前提知識

  * EC2も基本知識（インスタンス起動、VPCの設定、SSH接続）がわかっていること
  * Gitの知識
  * CodeCommitの基本知識（Gitリポジトリの作成、pushとか）
  * 東京リージョン（ap-northeast-1）

## 構成

構成についても再掲になるが、下記の通り。

![](../../../../gridsome-theme/src/assets/images/old/wordpress/785d0628.png)
（created with cloudcraft.io）

やりたいこととしては以下のような流れを実現すること。 

  * 開発者がコードをCodeCommitにpushする
  * コードのpushを検知してCodeBuildが走る
  * Build結果のコード一式をCodeDeployを使用してEC2にデプロイ
  
今回は簡易化のため、CodeBuildフェーズではUnitテストは走らせず、素通りするだけ。 やるにしても、CodeBuildさえ通過するようにしておけば、その中で（仮にLaravelなら）`mv .env.dev .env`して、`composer install`して、`vendor/bin/phpunit`するだけなので特に悩むところはないはず。 

## 下準備

### EC2の起動

![](../../../../gridsome-theme/src/assets/images/old/wordpress/107b76b5-800x439.png)

今回は無料枠対象のインスタンスを使用する。

ミドルウェアのインストールはAmazonのチュートリアルを参考にして準備する。
  
[チュートリアル: Amazon Linux 2 に LAMP ウェブサーバーをインストールする][2]

apacheのインストール、起動完了後、EC2のpublicIPにアクセスして、apacheが正常に動作していることを確認する。

![](../../../../gridsome-theme/src/assets/images/old/wordpress/8a5354ba-800x222.png)

その後、ドキュメントルート（デフォルトなら/var/www/html）にindex.phpを作成し、テストコードを記述しておく。 

```php
<?php
echo 'テストページ';</code></pre>
```

表示後

![](../../../../gridsome-theme/src/assets/images/old/wordpress/28e30c49-800x368.png)

### CodeCommitへのpush

CodeCommitで適当なリポジトリを作成して、先程のindex.phpをpushする。

![](../../../../gridsome-theme/src/assets/images/old/wordpress/f510b625-800x226.png)

### CodeBuildの準備

適当なビルドプロジェクトを作成する。CodePipelineで詳細な設定を行うため、環境情報（使用するコンテナイメージ等）以外は適当でも特に問題無し。

![](../../../../gridsome-theme/src/assets/images/old/wordpress/433d3b85-800x408.png)

CodeBuildの設定ファイルであるbuildspec.ymlは下記の通り 

```yaml
version: 0.2

phases:
  install:
    runtime-versions:
      docker: 18
  build:
    commands:
      - echo building...
artifacts:
  files:
    - '**/*'
```

### Codeployエージェントのインストール

先程作成したEC2インスタンスにSSH接続し、CodeDeploy用のエージェントをインストールする(東京リージョンの場合)。 

```bash
$ sudo yum update
$ sudo yum install ruby
$ sudo yum install wget
$ cd /home/ec2-user
$ wget https://aws-codedeploy-ap-northeast-1.s3.ap-northeast-1.amazonaws.com/latest/install
$ chmod +x ./install
$ sudo ./install auto
# エージェントのインストールが正常に行われていることを確認
$ sudo service codedeploy-agent status
```

エージェントをインストールしないとデプロイが一生成功しないので注意 

### CodeDeployのアプリケーションを作成

コンピューティングプラットフォームは「EC2/オンプレミス」を設定する。 デプロイグループを作成する。

![](../../../../gridsome-theme/src/assets/images/old/wordpress/56104b2b-800x361.png)

![](../../../../gridsome-theme/src/assets/images/old/wordpress/1f61a6a2-800x392.png)

![](../../../../gridsome-theme/src/assets/images/old/wordpress/9b227dc9-800x312.png)

※EC2インスタンスにはタグによって識別されるため、予め設定しておく。 

## CodePipelineの作成

### パイプラインの作成

ソースステージでは、ソースプロバイダーに先ほど作成したCodeCommitリポジトリを指定する。

ビルドステージは下記の通り、作成したビルドプロジェクト名を指定する。

![](../../../../gridsome-theme/src/assets/images/old/wordpress/af4e28f8-800x353.png)

デプロイステージは後で設定するので「導入段階をスキップ」する。 

### 詳細設定

上記の作成を終えると勝手にビルドが走るが、デプロイ設定をしていないのでまだデプロイは実行されない。

ここで、デプロイステージを追加するために、一番下の「ステージを追加する」を押下する。 ステージ名は「Deploy」を設定する。

追加されたステージの「アクショングループを追加する」を押下し、下記の通り入力。

![](../../../../gridsome-theme/src/assets/images/old/wordpress/07d0acb7-800x413.png)

※サービスロールはユースケース「CodeDeploy」を選択して作成したものを指定（AmazonS3FullAccessをアタッチしておく）。 

### CodeDeploy用Appspecの作成

CodeDeployにおいて、ソースの配置先や配置後の実行コマンドを指定したappspec.ymlを書きの通り作成し、pushしておく。 

```yaml
version: 0.0
os: linux
files:
  - source: /
    destination: var/www/html
```

### IAMロールの設定

デプロイ対象のEC2のインスタンスに、CodeDeployエージェント用の権限を設定したIAMロールをアタッチし、CodeBuildエージェントを再起動する。

![](../../../../gridsome-theme/src/assets/images/old/wordpress/924e0e67-800x384.png)

```bash
$ sudo service codedeploy-agent restart
```

## デプロイしてみる

index.phpを適当な文言に変更して、pushしてみる。

![](../../../../gridsome-theme/src/assets/images/old/wordpress/4c96f2ad-800x302.png)

めちゃくちゃ見づらいが、更新されていることがわかる。 

<hr class="wp-block-separator" />

今回はマネージドコンテナを使用してCodeBuildを走らせ、それをCodeDeployによってEC2にデプロイしてみた。

マネージドではなく好きなコンテナを使用したい場合には、前回の記事のようにdockerイメージをECRにpushすることでCodeBuildで利用することができる。

また、buildspec.ymlにおいて好きなshellを叩けるので.envファイルを環境ごとに配置したりわりと自由自在に操作可能である。

 [2]: https://docs.aws.amazon.com/ja_jp/AWSEC2/latest/UserGuide/ec2-lamp-amazon-linux-2.html
