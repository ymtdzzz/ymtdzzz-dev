---
title: "MKCertで手軽にローカル開発環境をSSL化する"
date: 2019-12-20
tags: 
  - "HTTPS"
  - "MKCert"
  - "OSS"
  - "SSL"
published: True
category: Infrastructure
---
## ローカルのSSL化

普段開発をしていると、ローカル開発環境はSSLを使用せずに構築することが結構ある。環境変数でSSLの使用不使用を振り分ける処理は、できれば無い方がいいのはたしか。 

<!--more-->

### オレオレ証明書

ローカル開発環境をSSL化するためによくあるのが「オレオレ証明書」を作成することである。 

[オレオレ証明書をopensslで作る（詳細版） &#8211; ろば電子が詰まつてゐる][1]

ただ、そんなに頻繁に開発環境構築を行わないため、毎回手順を確認してコマンドを叩くのもめんどくさい。

あと、認証局とサーバの秘密キーが同じ（オレオレ）なので、一応SSLは使えるが警告が出るのでなんか気になる。

さらに、ワイルドカード証明書を作成するにはさらにひと手間必要となる。 

### MKCert

そこで、もっと手軽に証明書を作成する方法を調べたところ、「**MKCert**」が良さげみたいだったので紹介する。

[GitHub &#8211; FiloSottile/mkcert: A simple zero-config tool to make locally trusted development certificates with any names you&#8217;d like.][2]

このツールの優れた点は、信頼された認証局も作成してくれるので、SSL接続時に警告が表示されることがない点。いいね。 

### MKCertの使用方法

#### インストール

```sh
# brewでインストール
$ brew install mkcert

# ローカル認証局の作成
$ mkcert -install
```

WindowsでもChocolateyかScoopでインストールできる。 

```sh
# chocolateyの場合
$ choco install mkcert

# Scoopの場合
$ scoop bucket add extras
$ scoop install mkcert
```

#### SSL証明書作成 証明書を作成したいドメイン名を指定すれば作成できる。 

```sh
# 通常のドメイン
$ mkcert example.com test.com

# ワイルドカード
$ mkcert "*.example.com"
```

すると、カレントディレクトリに*.pemファイルが作成される。 

#### webサーバ側の設定

pemファイルをサーバ内の任意のディレクトリに配置し、ssl.conf等に設定を追加する。 例は、localhostでpemファイルを作成した場合。 

```bash
SSLCertificateFile /etc/httpd/conf/localhost.pem
SSLCertificateKeyFile /etc/httpd/conf/localhost-key.pem
```

以上。えっ、めっちゃお手軽・・・。 

### ローカル開発環境にSSL接続可能になる

設定を終えたらhttpsで任意の先程作成した証明書のドメインにアクセスする。


![](/images/old/wordpress/46a4e1dd.png)

警告が出ることもなく、信頼された証明書としてちゃんと認識される。 

<hr class="wp-block-separator" />

このくらい手軽にできれば、環境構築用のshellとかも作れて良さそう。 プライベートの開発ではmkcertでHTTPS化してやってる。

 [1]: https://ozuma.hatenablog.jp/entry/20130511/1368284304
 [2]: https://github.com/FiloSottile/mkcert
