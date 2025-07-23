---
title: asdfのおすすめrustプラグイン
date: 2025-07-23
tags:
  - rust
published: true
category: Programming
---

久々にRustを触っていたときに一瞬ハマったのでメモしておきます。

asdfでRustを管理する場合、真っ先に思いつくのは[asdf-community/asdf-rust](https://github.com/asdf-community/asdf-rust)です。しかし、これを使ってRustをインストールする場合、Language Serverに必要な標準ライブラリのソースコードが入ってこないことがわかりました。

[question - how to get stdlib sources for intellij? · Issue #18 · asdf-community/asdf-rust](https://github.com/asdf-community/asdf-rust/issues/18)

少し調査したところ、上記issueでも言及がある通り[code-lever/asdf-rust](https://github.com/code-lever/asdf-rust)を使うのが良さそうでした。

ただし、`rust-analyzer`は下記の手順で自分で入れる必要があるっぽいのでそこは注意が必要です。

```
rustup component add rust-analyzer
```

これでLSPで補完が効くようになりました。めでたしめでたし。