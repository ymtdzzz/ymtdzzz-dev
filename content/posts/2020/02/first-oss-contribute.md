---
title: "はじめてのOSS contribute"
date: 2020-02-11
tags:
  - "Boostnote"
  - "Electron"
  - "github"
  - "OSS"
  - "React"
published: True
category: Diary
---
最近、長らく使っていたエンジニア向けノートアプリ「Boostnote」がリニューアルされた。それによってリポジトリも新しくなったみたいで、ソースコードもほぼ別物になったっぽい。実際に使ってみると色々バグも多くて、これはプルリクチャンスか？と思い、解決できるissueが無いか探してみた。

<!--more-->

## テーブルの表示バグ

使ってみて真っ先に目についたバグが、テーブルのmarkdownプレビューがテーマによって真っ白になってしまう事象。 

![](/images/old/wordpress/Boost-Note-2020-02-11-15-19-15-800x242.png)

すでにissueが切られてた。 [Table content not visible for preview in dark mode][1] 

### ソースコードの修正

まず、Boostnote.Nextリポジトリをforkして、ローカルにcloneする。その後、readmeに沿って開発環境を構築する。 

実際に弄りながらソースを確認し、修正箇所を明らかにする。 

/src/components/GlobalStyle.tsx 

```tsx
th,
td {
${backgroundColor}
}
```

テーブルの背景色をテーマ色に設定しただけ。 

### pull request発行

[Fix #309][2] 

![](/images/old/wordpress/344879805f2187a5b657a81dd32075f8-800x655.png)

ソースの変更内容をforkしたリポジトリにpushする。すると、気の利いたgithubがプルリク作成をsuggestしてくるので、プルリクを作成する。 

見た目の変更であれば、before/afterでスクリーンショットを貼り付けてわかりやすくしておくことで、レビュアーが内容を確認しやすいようにする。 

### 無事マージ

![](/images/old/wordpress/168a11baad877ef2337bc9050df2c93d-800x223.png)

数日後、無事マージ。 

## 初contribute

初めてのOSS貢献だったが、想像していたよりもスムーズに行うことができた。 

これまではなんとなくハードルが高そうなイメージだったけど、今後はあまり深く考えずに積極的に貢献していきたい。

 [1]: https://github.com/BoostIO/BoostNote.next/issues/309
 [2]: https://github.com/BoostIO/BoostNote.next/pull/317
