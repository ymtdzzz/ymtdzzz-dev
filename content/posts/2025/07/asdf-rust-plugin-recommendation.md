---
title: asdfのrustプラグインのおすすめ
date: 2025-07-23
tags:
  - rust
published: true
category: Programming
---

久々にRustを触っていたときに一瞬ハマったのでメモしておく。

asdfでRustを管理する場合、真っ先に思いつくのは[asdf-community/asdf-rust](https://github.com/asdf-community/asdf-rust)である。

しかし、これを使ってRustをインストールする場合、Language Serverに必要な標準ライブラリのソースコードが入ってこないことがわかった。

[question - how to get stdlib sources for intellij? · Issue #18 · asdf-community/asdf-rust](https://github.com/asdf-community/asdf-rust/issues/18)

そのため、上記issueでも言及がある通り、[code-lever/asdf-rust](https://github.com/code-lever/asdf-rust)を使うのが良さそうだった。

ただし、`rust-analyzer`は下記の手順で自分で入れる必要があるっぽい。

```
rustup component add rust-analyzer
```