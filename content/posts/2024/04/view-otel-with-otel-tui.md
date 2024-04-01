---
title: OpenTelemetryをターミナルから閲覧できるツール「otel-tui」を作っている
date: 2024-04-01
tags:
 - OpenTelemetry
 - Go
 - TUI
 - 自作ツール
published: true
category: Programming
---

最近作り始めたツールで、OpenTelemetryのテレメトリをターミナル上で閲覧できるツールを作っているのでそのご紹介です。


[https://github.com/ymtdzzz/otel-tui](https://github.com/ymtdzzz/otel-tui)


目下実装中ですが、Traceシグナルについてはある程度扱えるようになってきたので記事にしておきます。


# Table of Contents


# 使い方


## 起動と疎通


stableな機能がまだそこまで無いので、今のところはgo runで実行します。


```shell
$ git clone https://github.com/ymtdzzz/otel-tui.git
$ cd otel-tui
$ go run ./...
```


起動するとlocalhost:4317をListenし始めるので、計装済みのアプリケーションの向き先を合わせた状態で起動します（ここでは[opentelemetry-demo](https://github.com/open-telemetry/opentelemetry-demo)を使用）。


すると、ずらずらとTraceが流れてくると思います。


![f6460ef8-2fa8-4a2e-8685-b2b802882de6.png](../../../../gridsome-theme/src/assets/images/notion/f6460ef8-2fa8-4a2e-8685-b2b802882de6.png)


## サービスレベルのTrace探索


ここで表示されるTraceはサービスレベルです（厳密には`service.name` attribute）。`/`キーでサービス名でフィルターをかけられます（部分一致）。


![fe0173fb-0d23-4b81-a0ff-6b74e5606488.png](../../../../gridsome-theme/src/assets/images/notion/fe0173fb-0d23-4b81-a0ff-6b74e5606488.png)


また、`d`キーでdetailsの方にフォーカスできるので、不要なツリーを閉じたりできます。


## Spanツリー探索


特定のTraceを選択（`Enter`）すると、該当TraceIDに紐付いたSpanツリーが表示されます。ナビゲーションがいけてなくて上下キーでのみカーソル移動できます。


![4312da1c-2183-4c70-939e-d3080519c2b8.png](../../../../gridsome-theme/src/assets/images/notion/4312da1c-2183-4c70-939e-d3080519c2b8.png)


ここでも詳細情報がdetailsに出てくるので、同じように情報を確認できます。ここは今後Linkとかログとかに飛べるようにしたい。


# なぜ作ったか


## ログと同じようにライトに扱いたい


従来のログは非構造化・構造化いずれにしろテキストベースです。基本的にそうしたログについてはtailで流したり何かファイルに出力してgrepしたりjqや[loggo](https://github.com/aurc/loggo)に食べさせたり、基本はコマンドラインベースで確認することが多いと思います。


OpenTelemetryで出力したテレメトリについても同じようなノリでサクッとコマンド叩いて起動して、テレメトリの探索はコマンドラインで完結するようにしたかったというのが大きいです。


## 類似ツールとの比較


開発時、ローカルでotelから出力されたテレメトリを確認するツールとして、既に下記のツールがあります。

- [jaeger](https://github.com/jaegertracing/jaeger)
- [otel-desktop-viewer](https://github.com/CtrlSpice/otel-desktop-viewer)

jaegerはall-in-oneコンテナもあるし機能的には申し分無いのですが、[otel-desktop-viewerの開発動機](https://github.com/CtrlSpice/otel-desktop-viewer?tab=readme-ov-file#why-does-this-exist)にあるように、コンテナへの依存や、UI的にも少しtoo muchな側面があります（色々なポートだったり自身のトレース出力、サービスマップなど）。


otel-desktop-viewerについてはotel-tui自体かなり影響を受けていて、デバッグ用途でとても使いやすく良いツールだと思っています。こちらはシングルバイナリで起動できますが、やはりブラウザで閲覧するアプローチです。また、複数サービスをローカルで起動する場合などある程度流量が増えてきた場合に動作の重さが目立ちます（※ちゃんとベンチマーク取った訳ではありません）。


とはいえどちらもローカルでのデバッグ用途では十分だと感じますし、otel-tuiが同じような機能を提供できるようになったとしても結局どちらを使うかは好みの問題になるかなと思っています（tigを使うかGitKrakenを使うか、k8s Web UIを使うかk9sを使うか　みたいな問題な気がする）。


自分的にはもっとサクサク動くツール使いたかったという感じです。


# アーキテクチャ


## 概要


otel-tuiはotel-desktop-viewerと同様、[OpenTelemetry Collector Builder (ocb)](https://github.com/open-telemetry/opentelemetry-collector/tree/main/cmd/builder)を用いて生成される独自コレクターとして実装されています。


![03d74e31-8f32-4de0-80ac-93230d41f2d0.png](../../../../gridsome-theme/src/assets/images/notion/03d74e31-8f32-4de0-80ac-93230d41f2d0.png)


これにより、OTLPを話すための処理については考える必要がなく、テレメトリの保存や表示といったメインロジックに集中することが可能になります。また、Receiverの差し替えも容易になります。


## データストア


画面表示に必要な情報は全て[`/tuiexporter/internal/telemetry`](https://github.com/ymtdzzz/otel-tui/tree/main/tuiexporter/internal/telemetry)[パッケージ](https://github.com/ymtdzzz/otel-tui/tree/main/tuiexporter/internal/telemetry)の`Store`structに集約しています。


```go
// Store is a store of trace spans
type Store struct {
	mut                 sync.Mutex
	filterSvc           string
	svcspans            SvcSpans
	svcspansFiltered    SvcSpans
	cache               *TraceCache
	updatedAt           time.Time
	maxServiceSpanCount int
}
```


また、Traceに紐付くSpanは非連続的で受信タイミングも様々なため受信順にキューに詰めていき、欲しいタイミングで最新の情報を素早く取ってこれるようキャッシュレイヤーを用意しています。


```go
// SpanDataMap is a map of span id to span data
// This is used to quickly look up a span by its id
type SpanDataMap map[string]*SpanData

// TraceSpanDataMap is a map of trace id to a slice of spans
// This is used to quickly look up all spans in a trace
type TraceSpanDataMap map[string][]*SpanData

// TraceServiceSpanDataMap is a map of trace id and service name to a slice of spans
// This is used to quickly look up all spans in a trace for a service
type TraceServiceSpanDataMap map[string]map[string][]*SpanData

// TraceCache is a cache of trace spans
type TraceCache struct {
	spanid2span    SpanDataMap
	traceid2spans  TraceSpanDataMap
	tracesvc2spans TraceServiceSpanDataMap
}
```


それぞれ画面表示に必要な「SpanIDからSpan」「TraceIDからそれに紐付くSpan」「TraceIDとサービス名からそれに紐付くSpan」という形でキューに溜まっているSpanへの参照を返すようなデータ構造になっています。


また、当該パッケージについてはptraceや`SpanData`のみに関心を寄せ、画面描画など他の依存関係を持たないようにしています。


![a71296e1-4835-4da7-8aba-0dd502558803.png](../../../../gridsome-theme/src/assets/images/notion/a71296e1-4835-4da7-8aba-0dd502558803.png)


## 画面描画


画面描画のロジックは[`/tuiexporter/internal/tui`](https://github.com/ymtdzzz/otel-tui/tree/main/tuiexporter/internal/tui)[パッケージ](https://github.com/ymtdzzz/otel-tui/tree/main/tuiexporter/internal/tui)に集約しています。なお、TUIに描画するライブラリとして[tview](https://github.com/rivo/tview)を採用しました。


画面表示のデータソースはstoreですが、画面の状態（フォーカスとか入力内容）とかは極力tviewの仕組みを利用しています。


（例えば検索フォームとか、コンポーネントのライフサイクルがここで全て完結しているので`input`はローカル変数として定義している）


```go
func (p *TUIPages) createTracePage(store *telemetry.Store) *tview.Flex {
	// ...

	input := ""
	inputConfirmed := ""
	search := tview.NewInputField().
		SetLabel("Service Name (/): ").
		SetFieldWidth(20)
	search.SetChangedFunc(func(text string) {
		// remove the suffix '/' from input because it is passed from SetInputCapture()
		if strings.HasSuffix(text, "/") {
			text = strings.TrimSuffix(text, "/")
			search.SetText(text)
		}
		input = text
	})
	search.SetDoneFunc(func(key tcell.Key) {
		if key == tcell.KeyEnter {
			inputConfirmed = input
			log.Println("search service name: ", inputConfirmed)
			store.ApplyFilterService(inputConfirmed)
		} else if key == tcell.KeyEsc {
			search.SetText(inputConfirmed)
		}
		p.setFocusFn(table)
	})

	// ...

	return page
}
```


filterとか一部storeに書いちゃってるところあるけど・・・


# 設計上の勘所


## パフォーマンス観点


### データのローテーション


データに対する何かしらの処理（検索や変換など）を行う上で、データ量の上限を引いておくことが重要なので比較的早いタイミングで実装しておきました。


```go
// https://github.com/ymtdzzz/otel-tui/blob/main/tuiexporter/internal/telemetry/store.go#L114-L157
// AddSpan adds a span to the store
func (s *Store) AddSpan(traces *ptrace.Traces) {
	s.mut.Lock()
	defer func() {
		s.updatedAt = time.Now()
		s.mut.Unlock()
	}()

	// ... incoming payloadを詰める処理

	// data rotation
	if len(s.svcspans) > s.maxServiceSpanCount {
		deleteSpans := s.svcspans[:len(s.svcspans)-s.maxServiceSpanCount]
		s.cache.DeleteCache(deleteSpans)
		s.svcspans = s.svcspans[len(s.svcspans)-s.maxServiceSpanCount:]
	}

	s.updateFilterService()
}
```


ここでキューから古いデータを追い出し、削除されたSpanに紐付くキャッシュも下記処理で削除します。


```go
// https://github.com/ymtdzzz/otel-tui/blob/main/tuiexporter/internal/telemetry/cache.go#L52-L72
// DeleteCache deletes a list of spans from the cache
func (c *TraceCache) DeleteCache(serviceSpans []*SpanData) {
	for _, ss := range serviceSpans {
		traceID := ss.Span.TraceID().String()
		sname, _ := ss.ResourceSpan.Resource().Attributes().Get("service.name")

		if spans, ok := c.GetSpansByTraceIDAndSvc(ss.Span.TraceID().String(), sname.AsString()); ok {
			for _, s := range spans {
				delete(c.spanid2span, s.Span.SpanID().String())
			}
		}
		delete(c.tracesvc2spans[traceID], sname.AsString())
		if len(c.tracesvc2spans[traceID]) == 0 {
			delete(c.tracesvc2spans, traceID)
			// trace IDに紐付くSpanを走査して個別削除すると処理コスト食うのでtrace IDに紐付くSpanが無くなったら一気に消す
			delete(c.traceid2spans, traceID)
		}
	}
}
```


### 画面描画とデータ更新の非同期化


データ更新は結構な頻度で行われるのと処理コストもそれなりに高めなので、画面描画は非同期に行うようにしています。


起動時に`refresh()`のgoroutineを実行しています。


```go
// Run starts the TUI application.
func (t *TUIApp) Run() error {
	go t.refresh()
	return t.app.Run()
}

// ...

func (t *TUIApp) refresh() {
	tick := time.NewTicker(refreshInterval)
	for {
		<-tick.C
		if t.refreshedAt.Before(t.store.UpdatedAt()) {
			t.app.Draw()
			t.refreshedAt = time.Now()
		}
	}
}
```


基本500msに一度更新しようとしますが、デバッグ用途だと当然データが流れてこないこともあるので、storeが更新された場合のみ再描画するようにしています。


## 保守性観点


### フラットなデータ構造


cacheでは各キーで引いてこれるようにしていますが、基本的には親か子かは考えずSpanをフラットに持ちつつ、ここぞというときに親子関係を再計算するようにしています（Traceグラフ表示時など）。


これはデータ追加時の処理コスト軽減もありますが、Span自体の到達順は完全にランダムだということが前提のため、木の生成は必要なときに必要なだけ行うようにしています。


# 難しかったところ


## Traceグラフの表示


確認したいTrace IDが渡されて、それに紐付くSpanの親子構造を加味しつつタイムラインに配置していく処理です。


（これをやるためにotel-tuiを作ったと行っても過言では無い）


// TBD: 画像貼る


Spanのデータ構造は子が`ParentSpanID`を持つ形のため、Trace IDに紐付くSpanを走査して一般的な木構造に変換しています。


```go
// https://github.com/ymtdzzz/otel-tui/blob/main/tuiexporter/internal/tui/component/timeline.go#L19
type spanTreeNode struct {
	span     *telemetry.SpanData
	label    string
	box      *tview.Box
	children []*spanTreeNode
}

// https://github.com/ymtdzzz/otel-tui/blob/main/tuiexporter/internal/tui/component/timeline.go#L201-L252
func newSpanTree(traceID string, cache *telemetry.TraceCache) (rootNodes []*spanTreeNode, duration time.Duration) {
	spans, ok := cache.GetSpansByTraceID(traceID)
	if !ok {
		return
	}

	start := time.Now().Add(time.Hour * 24)
	end := time.Time{}

	// store memo and calculate start and end time of the trace
	spanMemo := make(map[string]int)
	nodes := []*spanTreeNode{}
	for idx, span := range spans {
		nodes = append(nodes, &spanTreeNode{span: span})
		spanMemo[span.Span.SpanID().String()] = idx
		if span.Span.StartTimestamp().AsTime().Before(start) {
			start = span.Span.StartTimestamp().AsTime()
		}
		if span.Span.EndTimestamp().AsTime().After(end) {
			end = span.Span.EndTimestamp().AsTime()
		}
	}
	duration = end.Sub(start)

	// generate span tree
	for _, span := range spans {
		current := span.Span.SpanID().String()
		node := nodes[spanMemo[current]]
		st, en := span.Span.StartTimestamp().AsTime().Sub(start), span.Span.EndTimestamp().AsTime().Sub(start)
		d := en - st
		node.box = createSpan(current, duration, st, en)
		node.label = fmt.Sprintf("%s %s", span.Span.Name(), d.String())

		parent := span.Span.ParentSpanID().String()
		_, parentExists := cache.GetSpanByID(parent)
		if !parentExists {
			rootNodes = append(rootNodes, node)
			continue
		}
		parentIdx := spanMemo[parent]
		nodes[parentIdx].children = append(nodes[parentIdx].children, nodes[spanMemo[span.Span.SpanID().String()]])
	}

	// sort root spans by start time
	sort.SliceStable(rootNodes, func(i, j int) bool {
		return rootNodes[i].span.Span.StartTimestamp().AsTime().Before(
			rootNodes[j].span.Span.StartTimestamp().AsTime(),
		)
	})

	return rootNodes, duration
}
```


`newSpanTree()`でroot nodeの配列が返るので、後はその子を再帰的に辿っていき描画してあげるだけです（[ソースコード](https://github.com/ymtdzzz/otel-tui/blob/main/tuiexporter/internal/tui/component/timeline.go#L179C1-L199C2)）。


また、タイムラインのうちバーを描画する部分については、Widthから相対的に座標を割り出すことでほぼ正確に描画できるようにしています。


durationについても、場合によってはマイクロ秒レベルだったり秒レベルだったりなど時間単位が変わってくるので、できるだけ`time.Duration`の力を借りてよしなに表示しています。


# 今後の展望


まだまだやりたいことてんこもりなんですが、UI的な調整はやりつつ、まずはLog（とできればMetrics）やっていきたいと思っています。


また、開発者用のツールという位置付けなので、OTLP以外のreceiver（jsonベースの標準入力とか）対応だったり、例えばsemantic conventionに則っていないSpanに対する警告とかできたら面白いかもと想像しています。


どこかでちゃんとロードマップ引いてみようと思います。


また何か大きなアップデートあったら記事にしますが、もし何かフィードバックありましたらissueやTwitter（X）までお願いします。

