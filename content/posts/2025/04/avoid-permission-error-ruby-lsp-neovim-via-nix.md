---
title: Nix経由でインストールしたasdf+ruby-lsp+neovimでpermission errorが発生する場合の対応
date: 2025-04-27
tags:
  - Ruby
  - trouble-shooting
published: true
category: Programming
---
私は普段環境をすべてNix+Home Managerで管理しています。その際、以下の構成でruby-lspを構築しようとした場合にちょっとしたトラブルに見舞われたので、その解決方法についてメモしておきます。

# 構成

OSは`macOS Sequoia 15.4.1 arm64`で、以下のアプリで構成されています。

- `nvim`: nix経由でinstall
- `asdf`: nix経由でinstall
- `ruby`: asdf経由でinstall
- `ruby-lsp`: `gem install ruby-lsp`でinstall

# 遭遇した問題について

neovim上でruby-lspをセットアップした際、LSP起動時に以下のエラーが発生するようになりました。

```
"stderr"	"There was an error while trying to write to\n`/nix/store/hahlr71z547r89r44ynp2123flzmahdp-neovim-ruby-env/lib/ruby/gems/3.3.0/cache/bundler/git`.\nIt is likely that you need to grant write permissions for that path.\n"
```

ruby-lspでは「Composed Ruby LSP bundle」という仕組みが採用されており、`プロジェクトルート/.ruby-lsp`ディレクトリに

- ruby-lsp用の依存関係（`ruby-lsp-rails`など）
- プロジェクトで利用している依存関係

がマージされた状態でbundleが生成されます（参考：[Composed Ruby LSP bundle | Ruby LSP](https://shopify.github.io/ruby-lsp/composed-bundle.html)）。

また、gemのパスが`neovim-ruby-env`配下のnix storeで解決されている理由までは深掘っていませんが、恐らくneovim上でruby-envのような、asdfとは別の仕組みで解決しているのかなと思っています（違ったら教えてください）。

今回のエラーの直接的な原因はComposed bundleではなくgemのパスがnix storeになっている点（後者）かなと思いますが、プロジェクト配下のbundleではなくruby-lsp用の独立したbundle installが行われる点も重要な点かと思います。

# 解決方法

`.ruby-lsp`ディレクトリを覗いてみます。

```sh
❯ ls .ruby-lsp
Gemfile                 Gemfile.lock            last_updated            main_lockfile_hash
```

ここが起点で`bundle install`されそうなので、以下のコマンドでbundleのインストール先をローカルの`.bundle`にしてみます。

```sh
❯ bundle config --local path .bundle
```

これでruby-lspがneovim上でもきちんと動くようになりました。

---

Nixで環境を整備していると、特に自分のように仕事はMacOS、個人開発はLinuxのように複数環境を利用している場合にとても便利ですが、nix storeのimmutableな性質でハマることがたまりあります。

あまり遭遇するケースは多くなさそうですが、誰かの役に立ちましたら幸いです。