---
title: "Github CLIのbeta版を試す"
date: 2020-02-24
tags:
  - "cli"
  - "github"
published: True
category: Misc
---
## はじめに

先日、githubの公式CLIツールがbeta版としてリリースされた。 

githubはGUIでしか基本使わなかったので当然CLIもあるものと勝手に考えていたが、これまでGithubのCLIは「Hub」という非公式ツールがデファクトになっていたらしい。 

[いつの間にかGithub無料ユーザでもプライベートリポジトリの作成が無料になっていた][1]ので、最近はBitbucketからGithubに徐々に移行しつつある。せっかくなのでCLIもざっと触ってみたいと思う。 

<!--more-->

## インストール

各OS毎のインストール方法は以下の通り。 

### MacOS

```bash
brew install github/gh/gh
```

### Windows

[公式サイト][2] からダウンロードしたインストーラ(.msi)で導入するか、下記コマンドでscoopを使用してインストール。 

```bash
scoop bucket add github-gh https://github.com/cli/scoop-gh.git
scoop install gh
```

## アカウント認証

適当なコマンドを実行すると、最初にブラウザ経由でログイン認証を求められるので、「authorize github」を選択して続行する。 

```bash
$ gh issue list
Notice: authentication required
Press Enter to open github.com in your browser...
```

![](/images/old/wordpress/Authorize-application-2020-02-24-12-08-58.png)

## issue関連のコマンド

### create

issueを作成するコマンド。対話形式でissueを作成することができる。 

```bash
$ gh issue create

Creating issue in zeroclock/gh-cli-test

? Title issue test 001
? Body &lt;Received>
? What's next 
? Preview in browser What’s next?
```

で「Preview in browser」を選択すると、下記のようにブラウザで入力内容を確認できる。

![](/images/old/wordpress/738c9e8bbcbfe437f7b5d9ffcf692973-800x514.png)

「Submit」を選択すると、そのままissueが作成される。 

### list

issueをリスト表示するコマンド。 

```bash
$ gh issue list

Issues for zeroclock/gh-cli-test

#3  issue test 003
#2  issue test 002
#1  issue test 001
```

-sオプションで、ステータスによるフィルタも可能。 

```bash
$ gh issue list -s closed

Issues for zeroclock/gh-cli-test

#2  issue test 002
```

### status

自分に関連するissueのステータスを表示する。 

```bash
$ gh issue status

Relevant issues in zeroclock/gh-cli-test

Issues assigned to you
  There are no issues assigned to you

Issues mentioning you
  There are no issues mentioning you

Issues opened by you
  #3 issue test 003 about 4 minutes ago
  #1 issue test 001 about 5 minutes ago
```

### view

指定したnumber/urlのissueの内容を表示する。 ブラウザで表示したければ下記のコマンド。 

```bash
$ gh issue view 1
Opening https://github.com/zeroclock/gh-cli-test/issues/1 in your browser.
```

terminal内で表示したければ-pオプションを指定する。 

```bash
$ gh issue view 1 -p
issue test 001
opened by zeroclock. 0 comments.
  Github CLIから初めてのissue作成です。
View this issue on GitHub: https://github.com/zeroclock/gh-cli-test/issues/1
```

## pr関連のコマンド

### create

pull requestを作成する。作成の流れはissue作成時と同様。 

```bash
$ gh pr create

Creating pull request for fix/feature-test into master in zeroclock/gh-cli-test

? Title pull request test001
? Body &lt;Received>
? What's next? Preview in browser
Opening github.com/zeroclock/gh-cli-test/compare/master...fix/feature-test in your browser.
```

![](/images/old/wordpress/155a5c68c9135cc79f215d198479fd7b-800x561.png)

### list

pull requestのリストを表示する。issueと同様にフィルタリングも可能。 

```bash
$ gh pr list

Pull requests for zeroclock/gh-cli-test

#4  pull request test001  fix/feature-test
```

### checkout

pull requestをcheckoutする。 

```bash
$ git checkout master
Switched to branch 'master'
Your branch is up to date with 'origin/master'.
$ gh pr checkout 4
Switched to branch 'fix/feature-test'
Your branch is up to date with 'origin/fix/feature-test'.
Already up to date.
```

### status

自分に関連するpull requestのstatusを表示する。 

```bash
$ gh pr status

Relevant pull requests in zeroclock/gh-cli-test

Current branch
  #4  pull request test001 [fix/feature-test]

Created by you
  #4  pull request test001 [fix/feature-test]

Requesting a code review from you
  You have no pull requests to review
```

### view

こちらもissueと同様、ブラウザ上、またはterminal上でpull requestの内容を表示できる。

```bash
$ gh pr view 4 -p
pull request test001
zeroclock wants to merge 1 commit into master from fix/feature-test
  github cliからのpull requestテストです。
View this pull request on GitHub: https://github.com/zeroclock/gh-cli-test/pull/4
```

## 最後に

まだbeta版なのでこれから色々変わっていくものと思われるが、個人のプロジェクトでissueを発行しまくったり大量のissue/prをフィルタするときにはサクッとできていいかも？

今取り組んでいるモバイルアプリ開発もgithubで管理するつもりなので、機会があったら活用してみたい。

 [1]: https://jp.techcrunch.com/2019/01/08/2019-01-07-github-free-users-now-get-unlimited-private-repositories/
 [2]: https://cli.github.com/
