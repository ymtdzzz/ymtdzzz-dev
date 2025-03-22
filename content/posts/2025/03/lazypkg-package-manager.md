---
title: 横断的にパッケージ管理できるツール「lazypkg」を作った
date: 2024-12-17
tags:
  - Go
published: false
category: Tool
---
皆さんは各種パッケージマネージャーでインストールしたパッケージをどのように管理していますか？私は仕事ではMac、プライベートでの開発ではLinuxと環境が異なっているのもあり、ほとんどのツールや設定（dotfilesなど）をNix flake+Home Managerで管理しています。

しかし、どうしてもシュッと入れて試したいツールや特定のプロジェクトのみで利用するツール群については`brew`や`npm install -g`、`apt`のようなパッケージマネージャーで管理することも多いです。

複数のパッケージマネージャーを利用していると、網羅的にoutdatedなパッケージを把握することが難しくなりますし、各CLIのオプション引数も様々なので混乱しやすいです（例：`update`か`upgrade`どっちだっけ・・・？）

# lazypkgというTUIアプリを作った

そこで、ターミナル上でいい感じにパッケージマネージャー横断でバージョン確認＆アップデートができるツール「lazypkg」を作りました。

https://github.com/ymtdzzz/lazypkg

![](../../../../gridsome-theme/src/assets/images/obsidian/lazypkg-package-manager/attachment-20250322223053930.gif)

利用方法のイメージについては後述しますが、以下の機能を提供します。

- アップデート可能なパッケージの一覧表示
	- パッケージ名
	- 現在のバージョン
	- 新バージョン
- パッケージ単体のアップデート
- 全パッケージのアップデート

なお、対応しているパッケージマネージャーは以下の通りです（2025/3/22時点）。ただし、こちらも後述しますが拡張可能な設計にしているため、自分が使っていて必要になったり需要がありそうなら追加予定です。

- apt
- gem
- homebrew
- npm
- docker

※dockerについてはdocker hubのAPI制限回避のためデフォルトOFFになっています

# 使い方

## インストール

今の所Homebrewと`go install`経由でのインストール方法を用意しています。

```sh
# Homebrew
brew install ymtdzzz/tap/lazypkg

# go install
go install github.com/ymtdzzz/lazypkg@latest
```

`lazypkg -v`が叩ければOKです。

```sh
lazypkg -v
# -> lazypkg version 0.0.7
```

## 起動＆アップデート可能なパッケージの確認

`lazypkg`で起動すると、自動的に対応しているパッケージマネージャーを検知して、サイドバーにリストアップ＆アップデート確認が行われます。

このとき、`apt`のようにrootで実行が必要な場合はパスワード入力用のダイアログが表示されますので入力してEnterで続行します。

![](../../../../gridsome-theme/src/assets/images/obsidian/lazypkg-package-manager/attachment-20250322224339102.png)

※執筆前に全アプデしてしまったので以降はサンプルデータでのデモ画像です。

起動時点ではサイドバーにフォーカスがあたっています。

![](../../../../gridsome-theme/src/assets/images/obsidian/lazypkg-package-manager/attachment-20250322224632303.png)

この状態では主に以下の操作が可能です。

- `↑↓`or`jk`：パッケージマネージャーのフォーカスを移動
- `Enter`or`→`or`l`：右ペインのパッケージ一覧にフォーカスを移動
- `Space`：一括操作対象に今フォーカスされているパッケージマネージャーを加える
- `r`：今フォーカスされているパッケージマネージャーのアップデートを再確認する
- `u`：
	- （一括操作対象が無い場合）今フォーカスされているパッケージマネージャーの全パッケージをアップデートする
	- （一括操作対象が存在する場合）一括操作対象のパッケージマネージャーの全パッケージをアップデートする

なお、フォーカスの移動や複数選択、アップデート等の操作は右ペインのパッケージ一覧でもほぼ同じです。

色々ありますのでユースケース別に見ていきましょう。

## 特定のパッケージをアップデートする

homebrewで管理している`terraform`だけアップデートしたいとします。

サイドバーで`homebrew`にフォーカスを合わせ、`Enter or → or l`で右ペインのパッケージ一覧に遷移します。

![](../../../../gridsome-theme/src/assets/images/obsidian/lazypkg-package-manager/attachment-20250322225833481.png)

その後、`terraform`にフォーカスを合わせ、`u`を押下すると確認ダイアログが出てきます。

![](../../../../gridsome-theme/src/assets/images/obsidian/lazypkg-package-manager/attachment-20250322225932928.png)

`Enter`を押すことでパッケージアップデートが実行されます。実行ログは下段にリアルタイムで出力されます（`ctrl+j`、`ctrl+k`でスクロール可）。

※demoモードなので適当なログを出していますが、実際は`brew upgrade terraform`が実行されると思います。

![](../../../../gridsome-theme/src/assets/images/obsidian/lazypkg-package-manager/attachment-20250322230211551.png)

実行後はアップデートの再確認が行われ、アップデート済みの`terraform`はリストから排除されます。

## パッケージを複数選択してアップデートする

同じくパッケージ一覧で`Space`を押下すると、今フォーカスされているパッケージの横に`*`が付きます。`ffmpeg`、`terraform`、`wget`を選択してみます。

![](../../../../gridsome-theme/src/assets/images/obsidian/lazypkg-package-manager/attachment-20250322230550650.png)

この状態で`u`を押すと、確認ダイアログの後3つのパッケージが一括でアップデートされます。

## 特定のパッケージマネージャー配下のパッケージをすべてアップデートする

例えば`apt`配下のパッケージをすべてアップデートしたい場合を考えます。パッケージ一覧にフォーカスしている場合は、`Backspace or ← or h`でサイドバーに戻ります。

サイドバーで`apt`にフォーカスしている状態で`u`キーを押すと、確認ダイアログをはさんでapt配下のパッケージをすべて更新できます。

上記の他、パッケージ一覧で`a`キーを押下しても同じ結果が得られます。


以上が`lazypkg`の基本的な使い方です。以降はモチベーション的な話と実装についてのお話になります。

# 類似ツールがあるのになぜ作ったか

この手のツールとして有名なツールがすでにあります。それがtopgradeです。

https://github.com/topgrade-rs/topgrade

topgradeは対応しているパッケージマネージャーもとても多く優れたツールです。実際私もしばらく利用していました。

しかし、topgradeは「どのツールをどのバージョンにアップデートするか（できるか）」という情報を事前に提供してくれません。「とりあえず`topgrade`コマンドを叩いておけば最新化できる」というのはわかりやすくてそれはそれで良いと思いますが、私としては少し違った思想を持ったツールを作りたくなりました。

グローバルにインストールされたパッケージは、それぞれ管理方法（やオプション引数などのインターフェース仕様）の違いはあるものの、やりたいことは結局のところ

- インストールされているパッケージを確認したい
- アップデート可能なパッケージを確認したい
- アップデートしたいパッケージをアップデートしたい

これくらいかなと思います。これらの目的を満たすさえできればパッケージマネージャーが何であるかはどうでもよく、それらの管理方法の差異を全部lazypkgが吸収できればユーザー（自分）が快適にパッケージ管理を行えると考えました。

※今の所「ユーザー＝自分」ですが、lazypkgは今の所自分にとって欠かせないツールになっています

# 実装について

かなりまだ荒削りですが、実装について特筆すべき意思決定をご紹介します。なお、言語は一番馴染みのあるGolangを選んでいます。

## TUIフレームワークとしてbubbleteaを採用

lazypkg以外にもTUIツールは作っていて、今もメンテを続けている[otel-tui](https://github.com/ymtdzzz/otel-tui)についてはtviewを利用しています。

https://github.com/rivo/tview

otel-tuiについてはトレースのスパンをターミナル上でマッピングしてフレームグラフを表示する独自エンジンを実装するのに丁度良かったのでtviewを選択しました。

しかし、今回はElmアーキテクチャで状態管理を行うフレームワークであるbubbleteaを選択しました。

https://github.com/charmbracelet/bubbletea

実を言うとそこまできちんとPoCをした訳ではなく（個人開発なので・・・）、アップデートは少なくともパッケージ管理ツール単位で非同期で行うことを想定しており、そうなるとイベント駆動の方がやりやすいかな？と思ったからです。

Elmでは状態（Model）の変更はイベント（メッセージ）経由でのみ行えます。例えばパッケージのアップデートについても「アップデートの開始」と「アップデートの完了」で2種類のメッセージを定義しています。

```go
// https://github.com/ymtdzzz/lazypkg/blob/85b8a4e01fb5c5a75797f530e8893e871759104b/components/messages.go#L27C1-L36C2
type updatePackagesStartMsg struct {
	name string
	pkgs []string
}

type updatePackagesFinishMsg struct {
	name string
	pkgs []string
	err  error
}
```

アップデート完了時には当該パッケージのローディングのスピナーを非表示（＝状態の更新）にし、アップデート確認を再度行いたい（＝新たなメッセージの送信）ので以下のようになります。

```go
// https://github.com/ymtdzzz/lazypkg/blob/85b8a4e01fb5c5a75797f530e8893e871759104b/components/packages.go#L149-L157
	case updatePackagesFinishMsg:
		if msg.name == m.name {
			for _, pkg := range msg.pkgs {
				if i, ok := m.pkgToIdx[pkg]; ok {
					m.loading[i] = false
				}
			}
			cmds = append(cmds, m.getPackagesCmd())
		}
```

tviewではこうした状態管理のフローは自前で設計する必要がありカオスになりがちな印象ですが、bubbleteaでは仕組みが用意されているので道を踏み外しにくいです。

ただし、大規模なアプリになると扱うメッセージも増え、今の実装のようにメッセージが一つにずらずら書かれて各コンポーネントから参照する設計では無理が出てくると思います。

## 拡張可能な設計



# さいごに