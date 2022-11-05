---
title: PHPの依存関係を洗い出す方法
date: 2022-11-04
tags:
 - PHP
 - dependency-graph
published: true
category: Programming
---

既存のPHPアプリをマイクロサービス化なりでリアーキテクティングする際、該当クラスがどこに使われているのか知りたいので依存グラフ（dependency graph）をサクッと作れる方法を考えてみました。


PHPの静的コード解析ツールは色々あるのですが、どうしても特定のクラスに絞った依存関係を抽出してくれるところまでやってくれるツールがありませんでしたので、自作のスクリプトで痒いところになんとか手を届かせる方針で行きました。


# Table of Contents


# 使うツール


既存のツールと自作スクリプトと、grepなど細かいコマンドをひとつまみ使います。

- [dephpend](https://github.com/mihaeu/dephpend)
- [extract-dependency.go（自作スクリプト）](https://gist.github.com/ymtdzzz/f8b0eb3b69bc66b102b70953a994b30f)

# 抽出方法


では試しにCodeIgniterのソースコードでやってみます。


[https://github.com/bcit-ci/CodeIgniter](https://github.com/bcit-ci/CodeIgniter)


## 依存関係の全抽出


Cloneした後、ディレクトリ直下でdephpendを実行し、全Classの依存関係を出力させます。


```shell
$ docker run --rm -v $(pwd):/inspect mihaeu/dephpend:latest text /inspect > result.txt
```


実行後、カレントディレクトリに`result.txt`が出力されます。


```shell
$ head result.txt
Calendar_test --> CI_TestCase
Calendar_test --> CI_Calendar
Driver_test --> CI_TestCase
Driver_test --> Mock_Libraries_Driver
Parser_test --> CI_TestCase
Parser_test --> CI_Parser
Table_test --> CI_TestCase
Table_test --> Mock_Libraries_Table
Table_test --> DB_result_dummy
DB_result_dummy --> CI_DB_result
```


## 対象Classの依存関係のみ抽出


全Classの依存関係が抽出できたので、あとは抽出したいClassだけに絞った依存関係のみを抽出します。


出力結果から特定Classのみ抽出するためには、下記のような処理を行う必要があります。

1. 対象Classに依存しているClassを調べる
2. そのClassに依存しているClassを調べる
3. さらにそのClassに依存しているClassを調べる
4. …
5. 依存しているClassが無ければ終了

再帰的な処理を書いてあげればいけそうです。ということでGoで簡単なスクリプトを書いてみました。


```go
package main

import (
	"bufio"
	"flag"
	"fmt"
	"io/ioutil"
	"os"
	"regexp"
	"strings"
)

var (
	inputPath      string
	className      string
	outputPath     string
	dependingRegex                      = regexp.MustCompile(`---> .*Library$`)
	cache          map[string]ResultSet = map[string]ResultSet{}
)

type ResultSet struct {
	classNames []string
	rows       []string
}

func init() {
	flag.StringVar(&inputPath, "input", "", "input file path")
	flag.StringVar(&className, "class", "", "search class name")
	flag.StringVar(&outputPath, "output", "", "output file path")
}

func main() {
	flag.Parse()

	if inputPath == "" || className == "" || outputPath == "" {
		fmt.Println("all args cannot be empty.")
		flag.CommandLine.PrintDefaults()
		os.Exit(2)
	}

	data, err := ioutil.ReadFile(inputPath)
	if err != nil {
		panic(err)
	}
	content := string(data)

	_, rows := recur(className, content, []string{}, []string{})

	file, err := os.Create(outputPath)
	if err != nil {
		panic(err)
	}
	defer file.Close()
	for _, r := range rows {
		_, err := file.WriteString(fmt.Sprintln(r))
		if err != nil {
			panic(err)
		}
	}
}

// 引数classに依存するclassを再帰的に取得する
func recur(class string, input string, progClass, progRow []string) ([]string, []string) {
	classes, rows := findDependingClasses(class, input)
	// 依存するclassが存在しなければ終了
	if len(classes) == 0 {
		return progClass, progRow
	}
	progClass = append(progClass, classes...)
	progRow = append(progRow, rows...)
	// それぞれのclassについてさらにそれに依存したclassを求める
	for _, c := range classes {
		a, b := recur(c, input, []string{}, []string{})
		progClass = append(progClass, a...)
		progRow = append(progRow, b...)
	}
	return progClass, progRow
}

// 引数classに依存するclassを返す
func findDependingClasses(class string, input string) (resultClass, resultRow []string) {
	fmt.Printf("class: %s, input: %s\n", class, input)
	if val, ok := cache[class]; ok {
		fmt.Println("cache hit")
		return val.classNames, val.rows
	}
	regex := regexp.MustCompile(fmt.Sprintf(`--> .*%s$`, strings.ReplaceAll(class, `\`, `\/`)))
	scanner := bufio.NewScanner(strings.NewReader(input))
	for scanner.Scan() {
		row := scanner.Text()
		if regex.MatchString(row) {
			resultRow = append(resultRow, row)
			splitRow := strings.Split(row, "-->")
			resultClass = append(resultClass, strings.TrimSpace(splitRow[0]))
		}
	}
	cache[class] = ResultSet{
		classNames: resultClass,
		rows:       resultRow,
	}
	return
}
```


パフォーマンス周りはチューニングしていないので大きなコードベースでいけるかはわからないです。inputはglobalで良さそうとか、色々改善できそうなところはありますが一旦これで。


先程生成した`result.txt`を処理します。今回は適当に色々なClassから参照されてそうな`CI_TestCase`とかでやってみます。


```shell
$ go run main.go -class CI_TestCase -input result.txt -output output.txt
```


実行が完了すると、対象Classに再帰的に依存するClassのみが抽出され、`output.txt`として出力されます。


```shell
$ head output.txt
Calendar_test --> CI_TestCase
Driver_test --> CI_TestCase
Parser_test --> CI_TestCase
Table_test --> CI_TestCase
Session_test --> CI_TestCase
UserAgent_test --> CI_TestCase
Typography_test --> CI_TestCase
Upload_test --> CI_TestCase
Encryption_test --> CI_TestCase
Form_validation_test --> CI_TestCase
```


## 依存関係の可視化


最後に、mermaidで依存関係を可視化してみます。出力結果の`—>`を`—|>`に変換すれば良い感じに出力できそうです。


```shell
$ cat output.txt | sed -e 's/-->/--|>/g' > output-mermaid.txt
$ head output-mermaid.txt
Calendar_test --|> CI_TestCase
Driver_test --|> CI_TestCase
Parser_test --|> CI_TestCase
Table_test --|> CI_TestCase
Session_test --|> CI_TestCase
UserAgent_test --|> CI_TestCase
Typography_test --|> CI_TestCase
Upload_test --|> CI_TestCase
Encryption_test --|> CI_TestCase
Form_validation_test --|> CI_TestCase
```


置換したテキストをmermaid.jsで変換すると、こんな感じの依存グラフが完成します（あまりにも横長すぎたので一部抜粋）


![70dc8f7d-45d2-4c9d-900e-f3b366eadc92.png](../../../../gridsome-theme/src/assets/images/notion/70dc8f7d-45d2-4c9d-900e-f3b366eadc92.png)


確かに、グラフに存在するClassの依存先を辿っていくと今回選んだ`CI_TestCase`に行き着くことがわかります。


---


ということで、選んだClassを使用しているClassを再帰的にリストアップする方法を紹介してみました。リファクタとかライブラリの入れ替えや、実装変更による影響範囲を調査したい場合に有用な方法だと思います。


ただ、PHPなので（？）漏れることもあると思いますので、きちんとテストコードでカバレッジを確保しておくのもお忘れなく。

