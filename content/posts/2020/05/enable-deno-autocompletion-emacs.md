---
title: "Emacs で deno のコード補完を有効化する"
date: 2020-05-10
published: True
tags:
  - "emacs"
  - "deno"
  - "typescript"
  - "yarn"
  - "rust"
  - "language-server"
category: Editor
---

## Emacs で Deno

最近 Rust で色々 CLI ツールを作って遊んでいるのですが、そのつながりで Rust で書かれた javascript ランタイムである[Deno](https://github.com/denoland/deno)の Getting started をちまちまやっていました。

言語は Typescript なので Emacs の[Tide](https://github.com/ananthakumaran/tide)でコード自動補完を有効化していたのですが、Deno での import 方法が対応していません。

```ts
import { serve } from "https://deno.land/std@v0.42.0/http/server.ts";
// ↑ここで [An import path cannot end with a '. ts'extension.]
// もちろんインポートしたモジュールの自動補完も不可。
```

## tsconfig.ts の編集で解決

<!--more-->

[【deno】「An import path cannot end with a '. ts'extension.」のエラーを回避する方法](https://qiita.com/uki00a/items/817442b00dc8f3b5696d)

上記の記事で大体問題無いんですが、ディレクトリ指定が Linux のものになっていたりするので Mac 用に補足しつつまとめます。

#### `yarn`で`typescript-deno-plugin`をプロジェクトに追加

```sh
$ cd /path/to/my/deno/project
$ yarn add -D typescript-deno-plugin typescript
```

#### tsconfig.json に下記の記述を追加

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "deno": ["<deno の型定義ファイル(deno.d.ts)への相対パス>"],
      "https://*": [
        "<http でインストールしたパッケージのキャッシュディレクトリへの相対パス>"
      ],
      "http://*": [
        "<https でインストールしたパッケージのキャッシュディレクトリへの相対パス>"
      ]
    },
    "plugins": [
        { "name": "typescrip-deno-plugin" }
    ]
  }
}
```

キャッシュディレクトリは OS 毎に異なりますので注意です([参考](https://github.com/denoland/deno/pull/1763))。

| Linux | Windows| MacOS |
| --- | --- | --- |
| ${HMOE}/.cache/deno | C:\Users\%USERNAME%\AppData\Local\deno | $HOME/Library/Caches/deno |

ここでは各環境の deno キャッシュディレクトリを`CACHE_DIR`とします。

- deno の型定義ファイルへの相対パス

    `${CACHE_DIR}/lib.deno.d.ts`

- http でインストールしたパッケージへの相対パス

    `${CACHE_DIR}/deno/deps/http/*`

- https でインストールしたパッケージへの相対パス

    `${CACHE_DIR}/deno/deps/https/*`


特に相対パスの指定については間違えないように注意。記述後バッファを再読み込み（or Emacs 再起動）等をするときちんと反映されると思います。

## 一発で設定してくれる CLI ツール作った

やっぱり相対指定めんどくせー！てなったので、環境依存をクリアしつつ tsconfig.json の設定と yarn add してくれるパッケージを作りました。

[deno-ls-init](https://github.com/zeroclock/deno-ls-init)

Rust で書いたので今の所`cargo`からのインストールのみ対応しています。

```sh
# deno-ls-init のインストール
$ cargo install deno-ls-init
# プロジェクトフォルダに移動
$ cd /path/to/your/deno/project
# deno 用の設定を実行
$ denolsinit
```

元から`tsconfig.json`があっても既存部分は書き換えないのでご安心くださいませ。ただ、Mac でしかテストしていないので Windows とか Linux で動作おかしかったら issue とかでお願いします。

![doom emacs で deno 対応](../../../../gridsome-flex-markdown-starter/src/assets/images/old/images/20200510/doom-emacs-auto-completion.png)
