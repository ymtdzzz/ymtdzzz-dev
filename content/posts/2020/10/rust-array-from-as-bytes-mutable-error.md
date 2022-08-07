---
title: "【Rust】as_bytes()でcannot borrow as mutable(E0596)エラー"
date: 2020-10-30
tags:
  - "Rust"
  - "trouble-shooting"
published: True
category: Programming
---

## cannot borrow data in a \`&\` reference as mutable {#cannot-borrow-data-in-a-and-reference-as-mutable}

共通鍵関連で、DES暗号化をRustで実装しているんですが、そのときにちょっとハマりかけたのでメモ。
<!--more-->

```rust
fn main() {
    let mut src = "abc".to_string();
    let mut s = src.as_bytes();

    println!("{:08b}", &s[0]);
    set_bit(&mut s, 0);
    println!("↓");
    println!("{:08b}", &s[0]);
}

fn set_bit(bytes: &mut [u8], bit: usize) {
    bytes[bit / 8 as usize] |= 0x80 >> (bit % 8);
}
```

<div class="src-block-caption">
  <span class="src-block-number">Code 1</span>:
  問題となったコード
</div>

処理自体は単純で、文字列をbyte配列に変換後、指定されたビットを立てるような感じです。

ただ、このソースをコンパイルしようとすると、下記のようなエラーが発生します。

```nil
error[E0596]: cannot borrow data in a `&` reference as mutable
 --> src/main.rs:8:13
  |
8 |     set_bit(&mut s, 0);
  |             ^^^^^^ cannot borrow as mutable
```

<div class="src-block-caption">
  <span class="src-block-number">Code 2</span>:
  エラー内容
</div>


## 原因 {#原因}

[as\_bytes()の定義](https://moshg.github.io/rust-std-ja/std/primitive.str.html#method.as%5Fbytes)を確認すると、

> pub const fn as\_bytes(&self) -> &[u8]

`as_bytes()` の返り値はバイト配列への不変参照になるので、それを可変な変数に格納しても、 `set_bit()` でバイト配列には可変アクセスできないのでした。

![](../../../../gridsome-flex-markdown-starter/src/assets/images/old/ox-hugo/20201030_094537.png)


## 解決策 {#解決策}

今回の場合、unsafeなas\_bytes\_mut()を使用することで、バイト配列への可変参照を取得できます。

最終的には下記のようなソースにすることで、コンパイルが通ります。

```rust
fn main() {
    let mut src = "abc".to_string();
    let mut s = unsafe { src.as_bytes_mut() };

    println!("{:08b}", &s[0]);
    set_bit(&mut s, 0);
    println!("↓");
    println!("{:08b}", &s[0]);
}

fn set_bit(bytes: &mut [u8], bit: usize) {
    bytes[bit / 8 as usize] |= 0x80 >> (bit % 8);
}
```

<div class="src-block-caption">
  <span class="src-block-number">Code 3</span>:
  修正したコード
</div>

出力結果：

```nil
01100001
↓
11100001
```

<div class="src-block-caption">
  <span class="src-block-number">Code 4</span>:
  出力結果
</div>


## まとめ {#まとめ}

Rustを書き始めたときはちんぷんかんぷんでしたが、最近はメモリの状態を意識しながら書くことに慣れてきました。こういうしょうもないエラーもたまにやってしまいますが、トラブルシューティングはかなりスムーズにできるようになってきた気がします。
