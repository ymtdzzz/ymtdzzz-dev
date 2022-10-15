---
title: "Goのhot reloadにgo-taskを使ってみる"
date: 2020-07-08
tags:
  - "go"
  - "task"
  - "docker"
published: True
category: Programming
---

## Goでhot reloading {#goでhot-reloading}

作っているアプリのサーバサイドをGOで書いているので、[Realize](https://github.com/oxequa/realize)でhot reloadを実現しようと思ったのですが、 `GO111MODULE=off` にしないとgo getできなかったり、いざdocker-composeで `realize start --run` しようとすると下記のようなエラーが出たりと色々あれだったので、他に使えそうなパッケージが無いか探してみました。

<!--more-->

```nil
...
[01:09:01][SRC] : Running..
panic: runtime error: invalid memory address or nil pointer dereference
[signal SIGSEGV: segmentation violation code=0x1 addr=0x0 pc=0x4cf2fb]

goroutine 8768 [running]:
os.(*Process).signal(0x0, 0xad7a20, 0xe34878, 0x0, 0x0)
      /usr/local/go/src/os/exec_unix.go:56 +0x3b
os.(*Process).Signal(...)
      /usr/local/go/src/os/exec.go:131
github.com/oxequa/realize/realize.(*Project).run.func1(0xc000175698)
      /go/src/github.com/oxequa/realize/realize/projects.go:581 +0x5c
github.com/oxequa/realize/realize.(*Project).run(0xc0001fa000, 0xc000133ab8, 0x7, 0xc000342300, 0xc000110540, 0xad2c20, 0xc00011c8d0)
      /go/src/github.com/oxequa/realize/realize/projects.go:646 +0xc2d
github.com/oxequa/realize/realize.(*Project).Reload.func3(0xc0001fa000, 0xc000342300, 0xc000110540)
      /go/src/github.com/oxequa/realize/realize/projects.go:262 +0x147
created by github.com/oxequa/realize/realize.(*Project).Reload
      /go/src/github.com/oxequa/realize/realize/projects.go:260 +0x297
```

<div class="src-block-caption">
  <span class="src-block-number">Code 1</span>:
  docker-composeでrealize startした際のエラー
</div>

調べたところ、[go-task](https://github.com/go-task/task) が中々シンプルで良さそうだったので試してみました。


## go-taskの使い方 {#go-taskの使い方}

基本的な使い方は下記の通り。


### go-taskのインストール {#go-taskのインストール}

[ドキュメント](https://taskfile.dev/#/installation) にあるように、MacとLinux(Linuxbrew導入済)は `brew` で、Windowsの場合は `scoop` とかでサクッとインストールできるみたいです。

ただ、私の場合はdocker上のdebianでインストールしたかったので ~~dockerでlinuxbrew入れるの地味にめんどうなので~~ バイナリを `dpkg` でインストールしました。

```bash
wget https://github.com/go-task/task/releases/download/v2.8.1/task_linux_amd64.deb
dpkg -i task_linux_amd64.deb
rm task_linux_amd64.deb
```

<div class="src-block-caption">
  <span class="src-block-number">Code 2</span>:
  Debianにおいて、バイナリ(.deb)をdpkgでインストールするコマンド
</div>


### Taskfile.ymlの作成 {#taskfile-dot-ymlの作成}

go-taskでは諸々の設定をTaskfile.ymlに記述しますので、プロジェクトルートにTaskfile.ymlを作成します。 `task init` でサクッと作ってくれます。

```bash
cd /path/to/project/root
task init
```

ソースをウォッチして特定のコマンド（go runとか）を実行させたい場合、こんな感じに書けます

```yaml
version: '2'

tasks:
  run:
    cmds:
      - go run main.go
    sources:
      - ./**/*
```


### 実行 {#実行}

あとはTaskfile.ymlがあるディレクトリで実行するだけです。

```bash
# runはTaskfile.ymlで指定したタスク名
task run
```


## 自分の使い方 {#自分の使い方}

プレイベートで開発しているアプリが、Goで書いたローカルサーバでReactを配信する　といった構成になってます。Goのサーバはリソース配信用とAPI兼用になっており、開発中はDocker container上で動かします。シンプルな構成なのでついでに記載しておきます。

フォルダ構成（抜粋）は下記の通り。

![](../../../../gridsome-theme/src/assets/images/old/ox-hugo/overview.png)


### Dockerfile {#dockerfile}

npmも入れています。

```Dockerfile
FROM golang:1.14.4

WORKDIR /go/src

ENV GO111MODULE=on

pCOPY . /go/src

RUN apt-get update \
    && apt-get install -y git python jq curl \
    && curl -sL https://deb.nodesource.com/setup_14.x | bash - \
    && apt-get update && apt-get install -y nodejs \
    && npm install yarn -g \
    && wget https://github.com/go-task/task/releases/download/v2.8.1/task_linux_amd64.deb \
    && dpkg -i task_linux_amd64.deb \
    && rm task_linux_amd64.deb

EXPOSE 8080

CMD ["task", "run"]
```


### Taskfile {#taskfile}

```yaml
version: '2'

tasks:
  run:
    cmds:
      - cmd: kill -TERM `cat pidfile`
        ignore_error: true
      - go run main.go --pid-file=pidfile
    sources:
      - ./**/*
```

`go run main.go` だけだとフォルダ変更を検知する度に前に走っていたプロセスを落とさずにまた別プロセスとして起動してしまうので、pidを適当にどこかに吐き出しておいて、起動時は前のプロセスをkillしてから実行するようにしています（[go-taskでサーバーのライブリロードを実現する](https://qiita.com/croquette0212/items/dab91c1075c1f3ac7b8d) を参考にさせていただきました）。

これでファイル変更を検知してホットリロードしてくれます。


### 所感 {#所感}

環境構築というプロジェクトの本質に関わらない部分については、なるべくエネルギーを割きたくないのですが、go-taskのおかげで自分が作りたいものに集中できています。

実行済タスクのkillの仕方は若干ゴリっぽい側面があるので、もうちょいスマートにいけないか考え中です。ただ、Taskfile作ってコマンド叩くだけでいいというシンプルなワークフローは気に入ったので、しばらく使ってみたいと思います。
