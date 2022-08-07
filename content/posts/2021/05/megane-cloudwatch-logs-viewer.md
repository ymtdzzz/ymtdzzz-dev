---
title: "AWS Cloudwatch LogsのCLIビューワを作った"
date: 2021-05-23
tags:
  - "Rust"
  - "AWS"
  - "Cloudwatch"
  - "CLI"
published: True
category: Programming
---

ブログ更新サボってる間に色々ネタがたまってしまったのでちょこちょこ放出していきます。

いくつか作ったツールなどありますので、しばらくはそのあたりの紹介だったり、最近開発リーダー（PLじゃないよ）周りの仕事でアプリ設計だったり新しめのFWを使ったりしてるのでその辺の知見等も書けたらと思います。

とりあえず今回は作ったツールのお話。

<!--more-->


## モチベーション {#モチベーション}

業務でも日常的にAWS Cloudwatch Logsを見るわけなんですが、

-   Tailできない
-   複数のロググループを見るときに複数タブを開かないといけない
-   ロググループが増えてきたときにいちいち検索するのが面倒
-   そもそもWebで見るのが面倒

> そもそもWebで見るのが面倒

これについては、商用環境のAWSアカウントがIP制限付きのためログインの度にroleの引受（assume）をしないといけないというのがあります。

（単純にIP制限だけだと、裏でAWS側でリソースとってくるような場合にエラーになったりするので、ロール切替時にIPチェックをするようにしているため）

...と、色々「ブラウザでやんなくてよくね？」って思うことが多くなったので、せっかくなので作ってみたという。


## 作ったもの {#作ったもの}

こういうのを作りました。

[zeroclock/megane - GitHub](https://github.com/zeroclock/megane)

![](https://github.com/zeroclock/megane/raw/master/image/screenshot.png)

CLIでログをサクッと見れるツールになっています。

導入方法だったり使い方は `README` に書いてあるのですが、簡単に特徴を並べると下記のような感じです。

-   ログのTailが可能
-   最大4つまでロググループを表示
-   ログの折りたたみ＆展開
-   ロググループのインクリメンタルサーチ
-   選択中のログ全文をクリップボードにコピー
-   リージョン、プロファイルの切り替え
-   AssumeRole対応

今の所そこまで大した機能は無く、キーマップも微妙だったり色々荒削りではありますが、リリース時に複数サーバのログのTailを垂れ流したいときには使えるかなーと思います。

一応実案件でも使ってもらっており、色々FBもらって調整中です。


## 技術的な話 {#技術的な話}

言語はRustを使いました。ちょっと前からGoとかRust製のCLIツールが色々出てきたので、それに乗っかった形。

（ `peco` とか `gitui` とか色々有り難く使わせてもらってます ）

実装については、 `tokio` で非同期ゴリゴリです。UIについては[tui-rs](https://github.com/fdehau/tui-rs)を使用。

下記のような非同期タスクをspawnして、お互いにchannelを通じてイベントをやりとりしてログの取得だったりキー入力を捌いたりしています。

-   InputEventHandler : キー入力や、Tick（画面描画タイミング）を監視
-   LogEventEventHandler : ログデータ関連のイベントを監視（ログ検索イベント、取得したログ削除イベント等）
-   LogGroupEventHandler : ロググループ関連のイベントを監視（ロググループ検索イベント等）
-   MainEventHandler : キー入力やTickイベントが発生した場合に画面の再描画やキーイベントのハンドリングを行うメイン処理
-   TailLogEventEventHandler : ログのTail関連のイベントを監視（Tail開始/停止イベント、TailのTickイベント等）

UIについては下記のような `Drawable` トレイトを作って、それを実装するstructをUIパーツごとに作ってそれを組み合わせるといった感じにしています。

```rust
#[async_trait]
pub trait Drawable<B>
where
    B: Backend,
{
    /// all components must be drawable
    fn draw(&mut self, f: &mut Frame<'_, B>, area: Rect);

    /// handles input key event
    /// and returns if parent component should handle other events or not
    async fn handle_event(&mut self, event: KeyEvent) -> bool;

    /// push the key mappings for this component
    fn push_key_maps<'a>(
        &self,
        maps: &'a mut BTreeMap<KeyEventWrapper, String>,
    ) -> &'a mut BTreeMap<KeyEventWrapper, String> {
        maps
    }
}
```

<div class="src-block-caption">
  <span class="src-block-number">Code 1</span>:
  Drawableトレイト
</div>

それぞれ、画面描画処理（ `draw()` ）、キー入力イベントのハンドリング処理（ `handle_event()` ）、画面下部に表示されるキーマップのヘルプ情報の格納処理（ `push_key_maps` ）を実装するような構成にしました。

例えば、コード量の少ない `Help` だとこんな感じ（ `push_key_maps()` はデフォルト実装を使用 ）。

```rust
#[async_trait]
impl<B> Drawable<B> for Help<B>
where
    B: Backend + Send,
{
    fn draw(&mut self, f: &mut Frame<'_, B>, area: Rect) {
        let block = Block::default()
            .title("HELP".to_string())
            .borders(Borders::ALL);
        let paragraph = Paragraph::new(self.msg.as_ref())
            .block(block)
            .wrap(Wrap { trim: false });
        f.render_widget(paragraph, area);
    }

    async fn handle_event(&mut self, _event: KeyEvent) -> bool {
        false
    }
}
```

<div class="src-block-caption">
  <span class="src-block-number">Code 2</span>:
  Help構造体
</div>

ちなみに、 `handle_event()` で `bool` を返しているのは、UIパーツ（Component）によってはキーマップが競合することがあるので、その場合親Componentにキーイベントを伝播しないようにするためのフラグです。

描画のためのBackendもまんまBackendで定義しているおかげで、単体テストも簡単に書くことができます。

```rust
fn test_case(help: &mut Help<TestBackend>, lines: Vec<&str>) {
    let mut terminal = get_test_terminal(20, 10);
    let lines = if !lines.is_empty() {
        lines
    } else {
        vec![
            "┌HELP──────────────┐",
            "│                  │",
            "│test message      │",
            "│12345             │",
            "│                  │",
            "│                  │",
            "│                  │",
            "│                  │",
            "│                  │",
            "└──────────────────┘",
        ]
    };
    let expected = Buffer::with_lines(lines);
    terminal
        .draw(|f| {
            help.draw(f, f.size());
        })
        .unwrap();
    terminal.backend().assert_buffer(&expected);
}
```

<div class="src-block-caption">
  <span class="src-block-number">Code 3</span>:
  Help構造体の単体テスト
</div>

テスト用のBackendがtui-rsに付属してますので、それを使ってassertできます。


## おわりに {#おわりに}

最近こっちに時間割けて無いのであれですが、ちょこちょこ直しておこうと思います。

もし使ってくれた方いましたらissueとかでFBしてくださると助かります！
