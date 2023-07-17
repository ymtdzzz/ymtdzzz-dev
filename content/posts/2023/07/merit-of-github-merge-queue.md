---
title: Github Merge Queueの何が嬉しいのか
date: 2023-07-17
tags:
 - GithubActions
 - github
 - CI/CD
published: true
category: CI/CD
---

2023/7/12にGithub Merge QueueがGAになりました。


[https://github.blog/changelog/2023-07-12-pull-request-merge-queue-is-now-generally-available/](https://github.blog/changelog/2023-07-12-pull-request-merge-queue-is-now-generally-available/)


機能のパッと見はPRをただキューに積んでくれるだけで「何が嬉しいんだろう？」と思う人も多そうなので、何が嬉しいのか事例付きで紹介できればと思います。


# **TL;DR**

- 「PRの時点ではコンフリクトも無いしCIも通っているがマージしたらCI落ちた」というのが割とよくある
- 上記の対策として「マージ前にmain rebaseしてCIを再度回し、問題無いことを確認してからマージする」という作業を手動で行うしか無い
- Merge Queueを使用することでマージ後のCIチェックを自動化し、問題ある場合はマージせずに差し戻すことが可能になる

# Table of Contents


# 事例


ソースコードやプロジェクト設定の全貌は下記リポジトリをご参照ください。


[https://github.com/toolbox-labo/merge-queue-example](https://github.com/toolbox-labo/merge-queue-example)


## 前提


例えばこんなケースを想定してみましょう（よくある基本的なプロジェクトといった感じです）。

- 実装言語はGo言語
- 複数人で実装を行っているため、頻繁にPRがマージされる
- 単体テストを実装する文化があり、PRには必ずテストコード（追加 or 修正）が含まれる
- CI workflowが整備されたリポジトリのため、ブランチへのpush時にGithub Actionsによる単体テストが実行される

## 実装とテストコード


現実にこんなコードがあり得るかさておき、シンプルだが依存関係のある２つの関数を例にしてみます。名前と時間を渡すと、時間帯に即した挨拶文を表示する実装です。


```go
package main

import (
	"fmt"
	"time"
)

func main() {
	now := time.Now()
	fmt.Printf("%s", greeting("John", &now))
}

func getMSG(d *time.Time) string {
	if d.Hour() <= 12 {
		return "Good morning"
	}
	return "Good afternoon"
}

func greeting(name string, d *time.Time) string {
	return fmt.Sprintf("%s, %s", getMSG(d), name)
}
```


テストコードは下記の通りです。


```go
package main

import (
	"testing"
	"time"
)

func TestGetMSG(t *testing.T) {
	tests := []struct {
		name string
		time time.Time
		want string
	}{
		{
			name: "morning",
			time: time.Date(2023, time.July, 17, 12, 0, 0, 0, time.UTC),
			want: "Good morning",
		},
		{
			name: "afternoon",
			time: time.Date(2023, time.July, 17, 13, 0, 0, 1, time.UTC),
			want: "Good afternoon",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := getMSG(&tt.time)

			if tt.want != got {
				t.Errorf("Unexpected result. want: %s, got: %s", tt.want, got)
			}
		})
	}

}

func TestGreeting(t *testing.T) {
	afternoon := time.Date(2023, time.July, 17, 18, 0, 0, 0, time.UTC)

	tests := []struct {
		name string
		want string
	}{
		{
			name: "John",
			want: "Good afternoon, John",
		},
		{
			name: "Tarou",
			want: "Good afternoon, Tarou",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := greeting(tt.name, &afternoon)
			if tt.want != got {
				t.Errorf("Unexpected result. want: %s, got: %s", tt.want, got)
			}
		})
	}
}
```


また、すべてのbranch及びPRに対してCIを実行するworkflowも設定しています（[ソースコードはこちら](https://github.com/toolbox-labo/merge-queue-example/tree/main/.github/workflows)）。


# Merge Queueがあると助かるケース（これまで）


ではMerge Queueのメリットを享受できるケースを見ていきます。


まず、初期状態を下記の通りとします。


![cb5d1fb4-f4cc-4c21-95a8-7bb024da7b4d.png](../../../../gridsome-theme/src/assets/images/notion/cb5d1fb4-f4cc-4c21-95a8-7bb024da7b4d.png)


## Aさん）`greeting()`を修正


実際のPR: [https://github.com/toolbox-labo/merge-queue-example/pull/2](https://github.com/toolbox-labo/merge-queue-example/pull/2)


Aさんは新たにブランチをチェックアウトし、`greeting()`について、「引数`name`が`12`文字以上の場合、`Longname`という名前として扱われる」処理を追加したとします。


![4b2ed6bc-76c3-4bc8-8335-bf658ab23308.png](../../../../gridsome-theme/src/assets/images/notion/4b2ed6bc-76c3-4bc8-8335-bf658ab23308.png)


テストコードの修正も行ったため、CIで実行される単体テストは通っている状態です。


修正内容は下記の通りです。


```diff
diff --git a/main.go b/main.go
index 837822b..7cebeb4 100644
--- a/main.go
+++ b/main.go
@@ -18,5 +18,8 @@ func getMSG(d *time.Time) string {
 }
 
 func greeting(name string, d *time.Time) string {
+       if len(name) > 11 {
+               name = "Longname"
+       }
        return fmt.Sprintf("%s, %s", getMSG(d), name)
 }
diff --git a/main_test.go b/main_test.go
index 40cc491..2511e44 100644
--- a/main_test.go
+++ b/main_test.go
@@ -50,6 +50,10 @@ func TestGreeting(t *testing.T) {
                        name: "Tarou",
                        want: "Good afternoon, Tarou",
                },
+               {
+                       name: "TooLongName!", // over 11 chars => Longname
+                       want: "Good afternoon, Longname",
+               },
        }
 
        for _, tt := range tests {
```


## Bさん）`getMSG()`を修正


実際のPR: [https://github.com/toolbox-labo/merge-queue-example/pull/3](https://github.com/toolbox-labo/merge-queue-example/pull/3)


Bさんは、Aさんと同じタイミングでmainから作業ブランチをチェックアウトし、`getMSG()`について、「引数`d`が`18`時以降の場合`Good evening`を返す」処理を追加したとします。


![f9d34a6c-9b0f-4982-9978-e5b57e47095d.png](../../../../gridsome-theme/src/assets/images/notion/f9d34a6c-9b0f-4982-9978-e5b57e47095d.png)


修正内容は下記の通りです。


```diff
diff --git a/main.go b/main.go
index 837822b..ef894ad 100644
--- a/main.go
+++ b/main.go
@@ -13,6 +13,8 @@ func main() {
 func getMSG(d *time.Time) string {
        if d.Hour() <= 12 {
                return "Good morning"
+       } else if d.Hour() >= 18 {
+               return "Good evening"
        }
        return "Good afternoon"
 }
diff --git a/main_test.go b/main_test.go
index 40cc491..0c9c16d 100644
--- a/main_test.go
+++ b/main_test.go
@@ -21,6 +21,11 @@ func TestGetMSG(t *testing.T) {
                        time: time.Date(2023, time.July, 17, 13, 0, 0, 1, time.UTC),
                        want: "Good afternoon",
                },
+               {
+                       name: "evening",
+                       time: time.Date(2023, time.July, 17, 18, 0, 0, 1, time.UTC),
+                       want: "Good evening",
+               },
        }
 
        for _, tt := range tests {
@@ -36,7 +41,7 @@ func TestGetMSG(t *testing.T) {
 }
 
 func TestGreeting(t *testing.T) {
-       afternoon := time.Date(2023, time.July, 17, 18, 0, 0, 0, time.UTC)
+       evening := time.Date(2023, time.July, 17, 18, 0, 0, 0, time.UTC)
 
        tests := []struct {
                name string
@@ -44,17 +49,17 @@ func TestGreeting(t *testing.T) {
        }{
                {
                        name: "John",
-                       want: "Good afternoon, John",
+                       want: "Good evening, John",
                },
                {
                        name: "Tarou",
-                       want: "Good afternoon, Tarou",
+                       want: "Good evening, Tarou",
                },
        }
 
        for _, tt := range tests {
                t.Run(tt.name, func(t *testing.T) {
-                       got := greeting(tt.name, &afternoon)
+                       got := greeting(tt.name, &evening)
                        if tt.want != got {
                                t.Errorf("Unexpected result. want: %s, got: %s", tt.want, got)
```


## マージするとどうなるか


まず、それぞれのPRは互いにCIが通っています。この状態でマージするとどうなるでしょうか。


### Aさんの対応をマージ


![220f9930-1fc1-491f-a4d2-cef9d83e6c68.png](../../../../gridsome-theme/src/assets/images/notion/220f9930-1fc1-491f-a4d2-cef9d83e6c68.png)


マージ後のmainブランチのCIも通ります。


### Bさんの対応をマージ


続いてBさんのPRについても、特にコンフリクトすることなくマージすることが可能です。マージしてみましょう。


![62f2b824-0940-4813-ad82-4fb3a33de93c.png](../../../../gridsome-theme/src/assets/images/notion/62f2b824-0940-4813-ad82-4fb3a33de93c.png)


### mainでCI落ちた


はい、テストに失敗してCI落ちます。


![f7dd3b51-06a6-4f62-b1bd-cd9baea37a1e.png](../../../../gridsome-theme/src/assets/images/notion/f7dd3b51-06a6-4f62-b1bd-cd9baea37a1e.png)


エラー出力としては下記の通りで、Aさんの対応で追加されたテストケースにGood eveningの対応が考慮されてなかったためです。


```text
--- FAIL: TestGreeting (0.00s)
    --- FAIL: TestGreeting/TooLongName! (0.00s)
        main_test.go:68: Unexpected result. want: Good afternoon, Longname, got: Good evening, Longname
FAIL
FAIL	github.com/toolbox-labo/merge-queue-example	0.001s
FAIL
```


まとめると、

- 複数人で並行で作業している
- CIも通り、コンフリクトも発生しない
- 影響範囲が重複している

このような場合に今回のような事例が発生します。複数人で新規サービスや新機能をガリガリ作るフェーズで割とよくあるかと思います。


Merge Queueが無かったこれまでの運用では、PRのレビューが通ってコンフリクトが無いことを確認した後に手動でmaster rebaseするしか方法が無かったように思えます。


そこで、**Merge Queueの出番です**。


# Merge Queueがあると助かるケース（これから）


Merge Queueは、マージ対象のPRをキューに詰めてくれるだけでは無く、「マージ後のコードで特定のworkflowを流せる」機能があります。


実際に先程の例でやってみましょう！（先程のmerge commitは両方ともrevertしておきました）


## Branch protectionでMerge Queueを有効化


並列数は１にしておきます。また、`Merge Method`はマージ順で、最新のベースブランチにマージした状態でCIを動かしたいので`Squash and merge`か`Rebase and merge`を選択（違いについては[こちらの記事](https://medium.com/@ronnnnn_jp/github-%E3%81%AE-merge-queue-%E3%82%92%E8%A9%A6%E3%81%97%E3%81%A6%E3%81%BF%E3%81%A6%E5%88%86%E3%81%8B%E3%81%A3%E3%81%9F%E3%81%93%E3%81%A8-5c5b94cf477b)がわかりやすいです）。


![9a67aefd-fd7b-4982-95c3-20e1095ec812.png](../../../../gridsome-theme/src/assets/images/notion/9a67aefd-fd7b-4982-95c3-20e1095ec812.png)


## Github Actionsの設定


workflowも修正して、Merge Queueでマージされるタイミングで発火するようにtriggerを追加しておきます。


```diff
diff --git a/.github/workflows/ci.yaml b/.github/workflows/ci.yaml
index cc28123..4e9dff4 100644
--- a/.github/workflows/ci.yaml
+++ b/.github/workflows/ci.yaml
@@ -7,6 +7,9 @@ on:
   pull_request:
+  merge_group:
 
 jobs:
   ci:
```


## やってみる


先程のPRを復活させてやってみます。

- AさんのLongname対応: [https://github.com/toolbox-labo/merge-queue-example/pull/14](https://github.com/toolbox-labo/merge-queue-example/pull/14)
- Bさんのevening対応: [https://github.com/toolbox-labo/merge-queue-example/pull/15](https://github.com/toolbox-labo/merge-queue-example/pull/15)

RPを見ると、マージボタンが「Merge when ready」になってます。ではAさん、Bさんの順番で順にキューに詰めてみます。


想定通りAさんのPRはマージされ、BさんのPRはCI失敗により差し戻されることがわかります。


![13f0c533-ad9e-4abc-b93c-a796020e67af.png](../../../../gridsome-theme/src/assets/images/notion/13f0c533-ad9e-4abc-b93c-a796020e67af.png)


壊れた状態でmainにマージされずに済みました！ということで再度最新をrebaseして調整後、再度merge queueに追加すると、今度は問題無くマージされ、masterのCIもパスすることを確認できました。


# まとめ


「事故防止のためmain rebaseした状態で再度CIを回す」というのを手動ではなくmerge queueにやらせて、問題があるときだけ調整すれば良いというのは非常に楽ですし、理に適っているように感じます。


`Merge Method`やworkflowなどはチーム内での検討や調整は必要になりそうですが、実務でもどんどん導入していきたい機能だと思いました。


# 参考文献

- [https://docs.github.com/ja/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/merging-a-pull-request-with-a-merge-queue](https://docs.github.com/ja/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/merging-a-pull-request-with-a-merge-queue)
- [https://developer.mamezou-tech.com/blogs/2023/02/15/github-pr-merge-queue/](https://developer.mamezou-tech.com/blogs/2023/02/15/github-pr-merge-queue/)
- [https://medium.com/@ronnnnn_jp/github-の-merge-queue-を試してみて分かったこと-5c5b94cf477b](https://medium.com/@ronnnnn_jp/github-%E3%81%AE-merge-queue-%E3%82%92%E8%A9%A6%E3%81%97%E3%81%A6%E3%81%BF%E3%81%A6%E5%88%86%E3%81%8B%E3%81%A3%E3%81%9F%E3%81%93%E3%81%A8-5c5b94cf477b)
