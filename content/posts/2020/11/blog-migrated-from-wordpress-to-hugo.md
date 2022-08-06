---
title: "旧ブログの記事をこちらに移行しました"
date: 2020-11-10
tags:
  - "Other"
published: True
category: Diary
---

今回はちょっとしたお知らせです。

随分前からzeroclock.devを始めてはいたのですが、旧サイトの[ビボログ](https://vivolog.net)の記事はほったらかしだったのでこっちに持ってきました。

~~XServer高いので早く呪縛から開放されたかった~~

<!--more-->

当サイトはHugoとgithub.ioの組み合わせで、旧サイトはWordpressだったのでどうしたもんかなーと思い、色々調べてみたら[wordpress-to-hugo-exporter](https://github.com/SchumacherFM/wordpress-to-hugo-exporter)というプラグインを使ったらサクッと移行できました。

ざっと手順はこんな感じ。

> 1.  上記のgithubページからソースを丸ごとzipでダウンロード
> 2.  Wordpress管理画面から、ダウンロードしたzipを読み込んでプラグインを追加
> 3.  ツール＞Export to Hugoで丸ごとダウンロードされる

いらない画像とかも全部入ってるので、必要なものをピックアップしつつ、マークダウンも若干おかしいので手直ししつつ〜という感じで、そこまで苦労せずに移行できました。

ただ、記事数が多かったり画像が超多かったりするとメモリ不足で死ぬらしいので、その場合は下記の記事を参考に・・・。

[WordPressのBlogをHugoとNetlifyに移行する](https://randd.kwappa.net/2020/05/17/migrate-wordpress-to-hugo-and-netlify/)

移行完了したので、旧サイトは多分11月下旬あたりに閉鎖すると思われます。

ということで、今回はちょっとしたお知らせでした。
