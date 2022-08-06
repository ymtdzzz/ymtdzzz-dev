---
title: "EmacsのLSP-modeの動作を軽くする"
date: 2020-07-11
tags:
  - "Emacs"
  - "lspmode"
  - "performance"
published: True
category: Editor
---

EmacsのLSP-modeは非常に快適で、言語サポートの追加も簡単にできるので重宝しているのですが、動作がカクついたりしてストレスになる場合がありました。[ドキュメント](https://emacs-lsp.github.io/lsp-mode/page/performance/)を確認したところ、パフォーマンスチューニングの方法があったのでまとめておきます。

<!--more-->

## いざチューニング {#いざチューニング}

今回対応するチューニングが正常に適用されているかどうかは、 `M-x lsp-diagnose` で確認できます。

```nil
Checking for Native JSON support: OK
Checking emacs version has `read-process-output-max': OK
Using company-capf: OK
Check emacs supports `read-process-output-max': ERROR
Check `read-process-output-max' default has been changed from 4k: ERROR
Byte compiled against Native JSON (recompile lsp-mode if failing when Native JSON available): ERROR
`gc-cons-threshold' increased?: ERROR
```

<div class="src-block-caption">
  <span class="src-block-number">Code 1</span>:
  lsp-diagnoseの出力結果
</div>

以前company-capfだけ有効化していたので、 `Using company-capf` がOKになっていますが、company-lspを使用している場合はERRORになるかと思います。

また、私の環境はEmacs-plus@28でネイティブJSONパーサ（後述）入りでビルドしたものなので、 `Native JSON support` と `` emacs version has `read-process-ourput-max` `` がOKになっています。Emacs26とかだとERRORになるかもしれませんので、アップデートが必要です。

それでは実際に各チューニング内容を確認していきます。


### EmacsのネイティブJSONパーサを使う {#emacsのネイティブjsonパーサを使う}

Emacsはver.27以降は、ネイティブでJSONのパースをサポートするようになりました。

ただし、ver.27以降でも、コンパイル時に `--with-json` オプションが渡されていないとサポートされないみたいです。

自分が使用しているEmacsが対応しているかどうかは `M-: (functionp 'json-serialize)` で確認できます。

ちなみに、MacでEmacs-plusを使用する場合は、 `brew install emacs@28 --with-jansson` でインストールできます。

Elispのパーサよりも、ネイティブパーサの方が最大15倍程度まで高速化されるらしい(Benchmarks show that Emacs 27 is ~15 times faster than Emacs when using Elisp json parser implementation.)ので、この設定は絶対ON推奨です。


### gc-cons-threshold の調整 {#gc-cons-threshold-の調整}

`gc-cons-threshold` は、ガベージコレクションを実行する閾値ですが、デフォルト設定だとLSP-server/client間のデータやり取りに対して少なすぎるため、増やしてあげる必要があります。

調製の仕方は下記の２通り紹介されていました。

-   100mbくらいの大きな値をドカッと割り当てる（doomとかspacemacsとかも同じような設定）
-   初期設定を２倍していき、２倍してもレスポンスに変化が見られない時点で増加をストップさせ、それを設定値とする

後者の設定方法についてはGNU EmacsのメンテナであるEli Zaretskii氏のおすすめなので、一旦はこれに従って設定しました。

現在の設定値を確認するためには `M-x eval-expression gc-cons-threshold` で確認できます。ちなみに私の環境だと800,000(80KB)でした。

毎回init.elを書き換えて増やしていくのはめんどうなので、 `M-x eval-expression (seta gc-cons-threshold 1600000)` のような感じで少しずつ増やして様子を見てみたところ、丁度6,400,000と12,800,000の辺りでサジェストの出方がスムーズになり、それ以上増やしてもそこまで変化が無かったので、12,800,000(12MB)あたりにしておきました。


### company-lsp ではなく company-capf を使用する {#company-lsp-ではなく-company-capf-を使用する}

今はcompany-lspは非推奨になっているので、company-capfを使用する設定を行います。

ドキュメントだと `(setq lsp-prefer-capf t)` だけでいいとのことだったのですが、私の環境だとcompany-backendsにcompany-capfが入ってくれなかったので、 下記のように明示的に設定しています（use-packageでlsp-mode読み込んでるとこ）。

```elisp
:hook
(lsp-mode . lsp-ui-mode)
(lsp-managed-mode . (lambda () (setq-local company-backends '(company-capf))))
```

<div class="src-block-caption">
  <span class="src-block-number">Code 2</span>:
  明示的にcompany-capfを使用する設定
</div>

設定の確認は `M-x company-diag` でできます。


### (Windowsの場合)lsp-uiを無効化する {#windowsの場合--lsp-uiを無効化する}

Windowsだとlsp-uiが悪さをして遅くなることがあるみたいです。私はMacなのでスルー。


### lsp-idle-delay の調整 {#lsp-idle-delay-の調整}

タイピング中にどれくらいの頻度でLSP系の状態（ハイライトとか）を更新するかの値ですが、これはとりあえず初期値の0.5のままにしました。


## 最終確認 {#最終確認}

以上のチューニング完了後、再び `lsp-diagnose` を実行すると、下記のような出力になるかと思います。

```nil
Checking for Native JSON support: OK
Checking emacs version has `read-process-output-max': OK
Using company-capf: OK
Check emacs supports `read-process-output-max': OK
Check `read-process-output-max' default has been changed from 4k: OK
Byte compiled against Native JSON (recompile lsp-mode if failing when Native JSON available): OK
`gc-cons-threshold' increased?: OK
```

<div class="src-block-caption">
  <span class="src-block-number">Code 3</span>:
  やったぜ
</div>
