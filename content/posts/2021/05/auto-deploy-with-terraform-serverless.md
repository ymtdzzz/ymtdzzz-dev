---
title: "Serverless,ECS（Fargate）自動デプロイ環境の構築"
date: 2021-05-24
tags:
  - "AWS"
  - "Terraform"
  - "Serverless"
  - "CICD"
  - "Lambda"
  - "Laravel"
published: True
category: Infrastructure
---

デプロイを自動化するのがMustになりつつありますが、なかなか完璧な自動デプロイ環境を作るのは難しいなーと感じています。

で、最近、所属会社の経営層へのプレゼンのネタとして、中途半端にデプロイ自動化しているプロジェクトを、全リソース自動デプロイ化したら面白いんじゃね？という点で色々検証してみましたので、それについての記事になります。

<!--more-->


## 課題 {#課題}


### 現状 {#現状}

現状のデプロイ構成はこんな感じでした。

![](/images/old/ox-hugo/before-structure.png)

単純化するとこんな感じ。

![](/images/old/ox-hugo/before-simple-structure.png)

まとめると下記のような感じです。

-   アプリケーション（このプロジェクトではLaravelでした）のソースはデプロイ自動化できている
-   ミドルウェアの設定ファイルは手動デプロイ
-   サーバレス（Lambda）のソースは手動デプロイ
-   インフラの設定情報も当然手動でしか変更不可


### 現状の運用の辛い点 {#現状の運用の辛い点}

-   デプロイするリソースによって手順が変わる（レビュア、デプロイ担当者の負担増）
-   手動デプロイソースはGit管理できていない
-   インフラ設定が知らないうちに変わるリスク（現状の運用では発生していない）
-   オペミスリスク

と、やっぱりある程度システムが複雑になってくると結構辛い点が出てきます。


## 作ってみた {#作ってみた}

ということで、後述のツールを使って実際に全部自動化したものがこちら。

[github zeroclock/terraform-practice-01](https://github.com/zeroclock/terraform-practice-01)

それぞれ、 `infra` がTerraformの定義ファイルで、 `app` 配下がWebアプリ（Laravel）のソースと、サーバレス（Lambda）のソースになっています。


### 使うツール {#使うツール}

ソースとかインフラ系の設定ファイルを全てコード化するとどんなもんになるんだろうと思い、下記のツールを使って同じような環境を作ってみました。

-   [Terraform](https://www.terraform.io/)：パブリッククラウドのインフラ構成をコード化して自動構築してくれるツール
-   [Serverless framework](https://www.serverless.com/)：サーバレス系（Lambda,S3など）のインフラ構築とアプリソースのデプロイを自動化してくれるツール

似たようなツールを使ってますが、棲み分けとしては下記のような感じです。

-   複数のリソースから参照されるリソース：Terraform
-   特定のリソースからのみ参照されるリソース：Serverless

> For application-specific infrastructure, we suggest managing all the pieces with the Serverless Framework, for a few reasons.
>
> ...
>
> However, coupling shared infrastructure to a specific application isn’t correct. Shared infrastructure will usually get updated instead of re-created from scratch.

例えばWebサーバとLambda、それぞれに参照されるDBがあるとすると、WebサーバとDBは `Terraform` で定義し、Lambda関数とそれに関連するAPI Gatewayや実行ロール等は `Serverlss` で定義するような感じです。


### 構成 {#構成}

インフラ＆デプロイ構成は下記の通り。

![](/images/old/ox-hugo/after-structure.png)

![](/images/old/ox-hugo/after-simple-structure.png)

SQSとLambdaが連携してたり、Laravelでバッチ用のコンテナがあったりで色々それっぽく作りました。Laravelについては、パブリックリポジトリにしている関係でenv系を暗号化するライブラリを入れていたりしてますが構成はほぼプレーンな状態です。


### 苦労したところ {#苦労したところ}

インフラ定義についてはそれぞれのファイルを見ていただくとして、大変だったのがTravisCIを使ったECSへのデプロイ周り（Terraform/sls関係ないじゃんというツッコミは置いといて...）。

`container definition` とか `task definition` についてはデプロイ時ダイナミックに値を入れたりしないといけないので、 `infra/code_deploy` 配下のシェルスクリプトで若干力技で修正してapplyしています。

```sh
#!/bin/bash

# set -eux

TAG=$1
APP_NAME=$2
REGION=$3

# get current taskdef
# ref: https://github.com/aws/aws-cli/issues/3064#issuecomment-784614089
TASK_DEFINITION=$(aws ecs describe-task-definition --task-definition ${APP_NAME} --region ${REGION} \
      --query '{  containerDefinitions: taskDefinition.containerDefinitions,
                  family: taskDefinition.family,
                  taskRoleArn: taskDefinition.taskRoleArn,
                  executionRoleArn: taskDefinition.executionRoleArn,
                  networkMode: taskDefinition.networkMode,
                  volumes: taskDefinition.volumes,
                  placementConstraints: taskDefinition.placementConstraints,
                  requiresCompatibilities: taskDefinition.requiresCompatibilities,
                  cpu: taskDefinition.cpu,
                  memory: taskDefinition.memory}')
ORIGINAL_TEXT=$(echo $TASK_DEFINITION | jq '.containerDefinitions[] | .image' -r | uniq)
REPLACED_TEXT=$(echo ${ORIGINAL_TEXT} | sed -z "s/:\S*/:$TAG/g")
ORIGINAL_ARR=($(echo $ORIGINAL_TEXT))
REPLACED_ARR=($(echo $REPLACED_TEXT))

for i in $(seq 1 ${#ORIGINAL_ARR[@]})
do
  # escape
  ORIGIN=$(echo ${ORIGINAL_ARR[i-1]} | sed 's/\./\\\./g' | sed 's/\//\\\//g')
  REPLACED=$(echo ${REPLACED_ARR[i-1]} | sed 's/\./\\\./g' | sed 's/\//\\\//g')
  TASK_DEFINITION=$(echo $TASK_DEFINITION | sed -z s/$ORIGIN/$REPLACED/g)
done

echo $TASK_DEFINITION >&1
```

<div class="src-block-caption">
  <span class="src-block-number">Code Snippet 1</span>:
  新しいtask_definitionを発行するシェルスクリプト（infra/code_deploy/get_new_taskdef.sh）
</div>

ここがクリアできさえすれば、あとはポチポチブラウザでインフラ構築するような感覚で定義ファイル修正＆ `terraform apply` すれば良いので、わりと楽でした。


## 考察 {#考察}


### 良さそうな点 {#良さそうな点}

こうしてインフラ構成やミドル構成などまるっとデプロイ自動化することで、先程挙げた点が解消できそうだなと。

-   デプロイするリソースによって手順が変わる（レビュア、デプロイ担当者の負担増）

    →全てGit管理されているので、同じ手順（コードレビュー、デプロイ実行）でデプロイできる

-   手動デプロイソースはGit管理できていない

    →Git管理できている

-   インフラ設定が知らないうちに変わるリスク（現状の運用では発生していない）

    →変更契機がGitへのPush時のみに限定されるので、変更が追いやすい

-   オペミスリスク

    →自動デプロイなのでリスク軽減

他にも、きちんと作ればインフラのマイグレが簡単にできたり、色々良いことずくめな気がしています。


### 微妙なところ（リスク） {#微妙なところ-リスク}

ただし、リスクもあるかと思います。

-   学習コスト

    →自分はもともとserverless使ってたので1,2md程度でチュートリアルやるだけで一応動くものは作れましたが、馴染みがない人だと若干苦労しそう。

-   保守できる人が限定される可能性

    →学習コストにも関連しますが、Terraformやslsに詳しい人が社内で増えないとメンテナンスできる人が限定されてしまうリスクもありそう（これはモダン言語で作ったりすると起こるような問題に近い）。

-   デプロイ設計きちんとできるプロジェクトじゃないと難しい

    →普段からCodePipelineとかのサービス使って、それなりにデプロイフローを構築・運用できるチームじゃないと難しい面はあります。


## さいごに {#さいごに}

最近は `Infrastructure as Code` 的な感じで色々なリソースをコード化しようっていう動きが活発化しているので、普段やってる案件でも取り込めたら良いですね。

実際、インフラ担当になった案件ではLambdaを一部Serverlessによるデプロイに切り替えたりしていますが、わりといい感じな気がしています。

ただ、デプロイ自動化までできて50点だと思っており、そこからさらにテスト自動化までできてやっと及第点な感じがするので、まだまだ先は長い...
