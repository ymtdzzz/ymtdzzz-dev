---
title: "WebBundlesことはじめ"
date: 2020-01-04
tags:
  - "Chrome"
  - "Go"
  - "WebBundles"
published: True
category: Web
---
## WebBundles概要

WebBundlesとは、Webコンテンツ（HTML/css/js…）を単一のファイルにまとめる技術。

<!--more-->

[Chrome Dev Summit 2019][1]で発表された。 

まだ実験的機能のため、Chromeのみ＋開発者用設定が必要となる。 

この技術のポイントとして、WebBundlesによってバンドルされたファイルを一度ダウンロードしてしまえば、それをロードする媒体は何でもいいということ。

端末のローカルストレージやUSBメモリ、SDカードでも問題無く読み込んで表示することが可能。

また、バンドルされたコンテンツの出どころを署名として保証する機能も有している。 

AMPサイトのURLをオリジナルのURLとして表示するための「[Signed HTTP Exchanges][2]」を含む[Web packaging][3]技術の一部として提供されているらしい。 

今回は、そんなWebBundlesを手軽に試すことができるページ（[Get started with Web Bundles][4]）があったので、それを参考に、実際に手を動かしながらやってみる記事。パス通したり細かいところも補足しておく。 

## 下準備 Goは予め導入済みの想定。 

### go/bundleのインストール、PATH設定

まず、CLIツールである`go/bundle`パッケージをインストールする。 

```go
$ go get -u github.com/WICG/webpackage/go/bundle/cmd/...
```

PATHも通しておく（GOPATHについても設定している）。 

```bash
$ vim ~/.bash_profile

# 末尾に以下の2行を追加
export GOPATH="$HOME/go"
export PATH="$PATH:$GOPATH/bin"

$ source ~/.bash_profile

# インストール確認
$ gen-bundle
Please specify -primaryURL.
Usage of gen-bundle:
  -URLList string
        URL list file
  -baseURL string
        Base URL (used with -dir)
  -dir string
        Input directory
  -har string
        HTTP Archive (HAR) input file
  -headerOverride value
        Set additional response header, replacing any existing values
  -ignoreErrors
        Do not reject invalid input arguments
  -manifestURL string
        Manifest URL
  -o string
        Webbundle output file (default "out.wbn")
  -primaryURL string
        Primary URL
  -version string
        The webbundle format version (default "b1")
```

### サンプルプロジェクトのclone,パッケージインストール

今回は参考サイトに倣って、prectを使用したTodoアプリである「[preact-todomvc][5]」をバンドルしてみる。

gitリポジトリのcloneと、npmパッケージのインストールを行う。 

```bash
$ git clone https://github.com/developit/preact-todomvc.git
$ cd preact-todomvc
$ npm i
$ npm run build
```

### WebBundlesの作成

下記のコマンドを実行し、WebBundlesファイル（.wbn）を作成する。 

```bash
gen-bundle -dir build -baseURL https://preact-todom.vc/ -primaryURL https://preact-todom.vc/ -o todomvc.wbn
```

すると、oオプションで指定した名称のwbnファイルがカレントディレクトリに生成される。 

```bash
$ ls
README.md        package-lock.json   src
build            package.json        todomvc.wbn
node_modules        rollup.config.js    webpack.config.babel.js
```

## 作成したWebBundlesを実行する

wbnファイルの作成が完了したので、後はUSBメモリなりGoogleDriveなりお好みのデバイスで持ち運んだり、メールに添付して送信したり思いのまま扱うことが可能になる。

ただ、まだ実験的機能のため、動作確認のためにいくつか設定が必要になる。 

### WebBundlesの有効化

Google Chromeにて`chrome://version`にアクセスし、バージョンが80以降になっているか確認する。 

#### Google

Chromeのバージョンが79以下の場合 拡張機能[Chrome Canary][6]をインストールし、Chrome再起動で有効化する。 

#### 共通作業

`chrome://flags/#web-bundles`にアクセスし、Enabledに設定する。

![](/images/old/wordpress/d29d4974-800x168.png)

### 実際に表示してみる

ここまできたら、後はwbnファイルをChromeのウィンドウに投げ込むだけ。

![](/images/old/wordpress/a8152aac-800x271.png)

ローカルで実行しているのにも関わらず問題無くjavascriptが動作している。 

## まとめ

参考サイトで活用事例として提示されていた「Webゲームを友人とオフライン環境でシェアしよう！」っていうのにはイマイチ共感できなかったが、使い道は色々ある・・・のかなぁ？ 

位置付け的には・・・オフラインでも閲覧できるという点ではPWAと似ているのかしら。PWAはキャッシュを使用し、こちらはコンテンツ自体をバイナリファイルとしてローカルに保存する。 

オフラインで使用できるユーティリティアプリとかゲームとかをWebアプリとして作成して、ネイティブアプリのように配布したりできるのは良いかも。 

いずれにしてもまだ発表からそこまで時間が経ってない＆実験段階なので、今後の動向は見守っていきたいと思う。

 [1]: https://developer.chrome.com/devsummit/
 [2]: https://developers.google.com/web/updates/2018/11/signed-exchanges
 [3]: https://github.com/WICG/webpackage
 [4]: https://web.dev/web-bundles/
 [5]: https://github.com/developit/preact-todomvc.git
 [6]: https://www.google.com/chrome/canary/
