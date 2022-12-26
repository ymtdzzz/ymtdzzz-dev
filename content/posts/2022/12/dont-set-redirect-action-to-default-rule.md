---
title: 【GCP】Security Policyでdefault ruleにredirectは設定しない方が良い
date: 2022-12-26
tags:
 - GCP
 - CloudArmor
published: true
category: Infrastructure
---

仕事で困ったのでメモしておきます。


# 事象


下記のような、redirect actionをdefault ruleに設定したCloud Armor Security Policyを作成します。


```shell
$ gcloud compute security-policies create sample-policy
$ gcloud compute security-policies rules update 2147483647 \
  --security-policy sample-policy \
  --action "redirect" \
  --redirect-type "external-302" \
  --redirect-target "https://example.com"
```


Webコンソールだとこんな感じになります。


![aa11183d-06f1-4d12-890a-4cced909d93a.png](../../../../gridsome-theme/src/assets/images/notion/aa11183d-06f1-4d12-890a-4cced909d93a.png)


で、この状態でdefault ruleのactionをdeny(403)にしてみます。


```shell
$ gcloud compute security-policies rules update 2147483647 \
  --security-policy sample-policy \
  --action "deny-403"
```


すると、下記のエラーで失敗します。


```shell
ERROR: (gcloud.compute.security-policies.rules.update) Could not fetch resource:
 - Invalid value for field 'resource.redirectOptions': ''. Redirect options can only be specified if the action is redirect.
```


続いて、Webコンソールで編集してみます。


![3d7b81e6-cb5d-4c06-856f-d995060a8db2.png](../../../../gridsome-theme/src/assets/images/notion/3d7b81e6-cb5d-4c06-856f-d995060a8db2.png)


「デフォルトのルールアクション」＞「許可しない」＞「更新」


![0906f8d6-5750-489b-ac0e-36b0e1ded20a.png](../../../../gridsome-theme/src/assets/images/notion/0906f8d6-5750-489b-ac0e-36b0e1ded20a.png)


？？？？


# 多分


多分APIかgcloud CLI側のバグな気がしてます。多分。redirect actionのルールを変更する際に、自動的に`redirectOptions`に空文字渡ってしまう実装になってるとか。
（変更用のAPIなので、デフォルト値に空文字入っちゃってるとか・・・）


暇があったら[issue tracker](https://issuetracker.google.com/issues/new?component=1132263&hl=ja&template=1639085)に投げてみます。

