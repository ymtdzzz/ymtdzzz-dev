---
title: "AWS CodeDeployのHookスクリプトでソースを弄りたいとき"
date: 2020-02-11
tags:
  - "AWS"
  - "CodeDeploy"
  - "Hook"
  - "Laravel"
  - "shellscript"
published: True
category: Infrastructure
---
## Hookスクリプトの実行場所

CodeDeployでソースをデプロイするときには、appspec.ymlでソースと実行するHookスクリプトを指定する。 

<!--more-->

```yaml
version: 0.0
os: linux
files:
  - source: src
    destination: /tmp/project_root
hooks:
  AfterInstall:
    - location: hook/deploy.sh
      timeout: 300
      runas: root
```
      
ここで実行されるdeploy.shは、/tmp/project_root/hook/deploy.sh ではなく、/opt/codedeploy-agent/deployment-root/deployment-group-id/deployment-id/deployment-archive/hook/deploy.sh になる。 

そのため、hookスクリプトはデプロイバンドルに含めること。というのは[CodeDeployフックのベストプラクティス][1]にも説明がある通り。 

## デプロイ後にソースをいじりたい場合

Laravelプロジェクトをデプロイ時にartisanでキャッシュクリアをしたり、独自のバッチコマンドを流したい場合の例を見てみる。また、追加の要件として、配置するソースは「src_202002031200」のようにバージョニングし、ドキュメントルートへのパスはシンボリックリンクにする。 

appspec.ymlは先程のものを使用しているものとする。deploy.shは下記の通り。
（権限系はプロジェクトによって異なるため割愛） 

```bash
#!/bin/sh

DOCUMENT_ROOT=/var/www/html
DATETIME=`date '+%Y%m%d-%H%M%S'`
SRC_PATH="${DOCUMENT_ROOT}/src_${DATETIME}"
# ファイル移動
mv "/tmp/project_root" "${SRC_PATH}"
# キャッシュクリア
cd "${SRC_PATH}"
rm bootstrap/cache/config.php
su - ec2-user -c "cd ${SRC_PATH};php artisan config:cache"
su - ec2-user -c "cd ${SRC_PATH};php artisan original_batch:exec"
# シンボリックリンク張替え
rm "${DOCUMENT_ROOT}/src"
ln -s "${SRC_PATH}" "${DOCUMENT_ROOT}/src"
```

このhookが実行されると、ソースコードが/var/www/html/src_{日付}配下に展開後、キャッシュクリア等をした後にシンボリックリンクが更新される。 

このままだとバージョニングされたコードが無制限に溜まってしまうので、ローテートする処理も必要になる。もっとも、ソースコードをHookで色々いじるケースはそこまでないと思うが、ご参考まで。

 [1]: https://dev.classmethod.jp/cloud/aws/best-practice-of-code-deploy-hooks/
