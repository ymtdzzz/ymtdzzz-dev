---
title: "画像の diff を生成する rust ライブラリを書いた"
date: 2020-05-25
tags:
  - "rust"
  - "storybook"
  - "react"
  - "css"
published: True
category: Programming
---

## Rust で画像の比較画像を生成

個人的に今取り組んでいるプロジェクトで、画像の差分を取得する必要があったのですが、いまいちそれっぽいライブラリが見つかりませんでした。

[lcs-image-diff](https://crates.io/crates/lcs-image-diff)もありましたが、ちょっとイメージと違う。

イメージ的にはこう、差分があるピクセルだけピンポイントで検出してほしい。

元画像を比較画像で減算して、その後元画像を加算する感じかな。

## ライブラリ作成

ということで、ライブラリを作成しました。依存ライブラリとして画像処理ライブラリの[image](https://crates.io/crates/image)を使用しました。

<!--more-->

```rust
pub fn diff(before: &DynamicImage, after: &DynamicImage) -> Result<DynamicImage>
```

`Cargo.toml`の dependencies に書いてもらって、下記のような感じで使います。

```rust
let before = image::open("before.png");
let after = image::open("after.png");
let image_diff = image_diff::diff(&before, &after).unwrap();
image_diff.save("image_diff.png");
```

すると、下記のような感じで差分が検出されます。

![diff_sample](../../../../gridsome-flex-markdown-starter/src/assets/images/old/images/20200526/sample.png)

もちろん、サイズ違いの画像を読み込ませても使えます。

## TODO

このライブラリの実装としては、愚直にピクセルのバイト列を走査して比較を行い、差異があるなら`255,0,0(赤)`で該当ピクセルを置き換える形です。

メインのプロジェクトでは、場合によっては大きな画像（数千 px とか）をたくさん処理する可能性があるので、それに合わせて

- パフォーマンス測定
- アルゴリズム修正

をちょこちょこやっていくつもりです。

もしバグや改善点等ありましたら[issue](https://github.com/zeroclock/image-diff/issues)をたててもらえるとありがたいです。
