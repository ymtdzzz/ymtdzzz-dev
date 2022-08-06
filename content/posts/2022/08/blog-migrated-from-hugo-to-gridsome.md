---
title: "Blogを移行した"
date: 2022-08-06
tags:
  - "hugo"
  - "gridsome"
  - "github-pages"
  - "cloudflare"
published: true
category: Diary
---

本日、Blogを下記の通り移行しました。

- platform

Github pagesからCloudflare pagesへ

- framework

Hugoからgridsomeへ

## Why

- Hugoも良かったが、Vueに親和性の高いSSGフレームワークを使ってみたかったから
    - 特に自分でテーマ作ろうとかはなかったのですが、Vue使いの知り合いにテーマ使ってもらえそうな流れになったので（まだ具体的な話までは行ってないので適当なテーマ使ってます）

以上です。「ただ使ってみたかった」というのが大きかったかも。

## How

リポジトリを新規に作成して、テーマ（starter）はsubmodulesとして管理する方針にしました。テーマのconfigとかは修正する必要があるので一旦forkして、それを`git submodule add`してます。

リポジトリはこちら

[https://github.com/ymtdzzz/ymtdzzz-dev](https://github.com/ymtdzzz/ymtdzzz-dev)

### コンテンツ移行

どちらもmarkdownをデータソースとして選べるので、ほぼそのままコピーして持ってきました。

ただ、画像データは少し注意が必要で、画像データ自体は前述のリポジトリで管理したいのですが、gridsomeの参照先はsubmodules内のstaticディレクトリになるので、[README](https://github.com/ymtdzzz/ymtdzzz-dev#getting-started)にも書いてありますが、`gridsome build`する前にシンボリックリンクを貼ってあげる必要があります。

```bash
ln -s $(pwd)/images ./{submoduleとして取り込んだテーマ（starter）のリポジトリ}/static/images
```

### Cloudflare pages設定

基本的にテーマはstarterという名前だけあって、submodulesとして取り込むのではなくこれをベースにブログを作ってね（＝ブログコンテンツと同じリポジトリで管理してね）ということみたいです。

が、自分の場合は後々テーマを入れ替える可能性が高かったのでsubmodulesとして管理していたので、ビルド設定も少し工夫が必要でした。

最終的なビルド設定はこんな感じになりました。

- build command: `npm install -g yarn @gridsome/cli && ln -s $(pwd)/images ./gridsome-flex-markdown-starter/static/images && cd gridsome-flex-markdown-starter && yarn && gridsome build`
- build output directory: `/gridsome-flex-markdown-starter/dist`
- root directory: `/`

テンプレート設定にgridsomeもあるのですが、その場合rootにstarterのディレクトリ直下（この場合は`/gridsome-flex-markdown-starter`）にくる必要があるみたいでした。しかし、rootをそこにしてしまうとそこからしかmountされない（＝その親のcontentを見に行けない）ので、テンプレート設定を使わずにrootは`/`のままいく必要がありました。

ということで、手動でyarnとgridsomeを入れてシンボリックリンク張ってビルドするまでをワンライナーで書いています。

ビルド設定完了後はブランチでプレビューリンク作ってくれたり、本来はGithub actionsやCircleCIのようなツールを自前で使うような部分も全部やってくれるので非常に便利だと思いました。

### これから

今後は下記のような機能を追加できればもっと快適なブログになりそうだなーと思っています。

- mermaid.js表示
- 目次表示
- コードスニペットのキャプションやファイル名表示
- リンクのカード化

ひとまずはデプロイ＆移行完了ということで。引き続きよろしくお願いします。
