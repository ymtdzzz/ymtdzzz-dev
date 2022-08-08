---
title: "ClusterInformation: connectionis unauthorized: Unauthorized でnodeのdrainがstuckしたときの対応"
date: 2022-08-08
tags:
  - "kubernetes"
  - "trouble-shooting"
  - "calico"
published: true
category: Infrastructure
---

小粒ですが地味に困ったのでメモしておきます。

## Table of Contents

## 経緯

GKEのkubernetes clusterで、Node Poolの入れ替えを行いに際して旧ノードのdrainをしていたのですが、Podのevictで下記のような状態でstuckしてしまいました。

```bash
evicting pod default/hoge-app-778dffdc5f-phrqk
I0808 16:59:05.149163    5142 request.go:601] Waited for 1.101590291s due to client-side throttling, not priority and fairness, request: GET:https://xxx.xxx.xx.x/api/v1/namespaces/default/pods/hoge-app-778dffdc5f-27bbk
I0808 16:59:15.341998    5142 request.go:601] Waited for 1.302038959s due to client-side throttling, not priority and fairness, request: GET:https://xxx.xxx.xx.x/api/v1/namespaces/default/pods/hoge-app-778dffdc5f-27bbk
I0808 16:59:25.342320    5142 request.go:601] Waited for 1.302322917s due to client-side throttling, not priority and fairness, request: GET:https://xxx.xxx.xx.x/api/v1/namespaces/default/pods/hoge-app-778dffdc5f-27bbk
I0808 16:59:46.142335    5142 request.go:601] Waited for 1.115315708s due to client-side throttling, not priority and fairness, request: GET:https://xxx.xxx.xx.x/api/v1/namespaces/default/pods/hoge-app-778dffdc5f-phrqk
I0808 16:59:56.342390    5142 request.go:601] Waited for 1.310516417s due to client-side throttling, not priority and fairness, request: GET:https://xxx.xxx.xx.x/api/v1/namespaces/default/pods/hoge-app-778dffdc5f-vczbq
...
```

該当のpodをdescribeしてみると、どうやらevictが完了してpodをkillするときに下記のエラーが発生しているようでした。

```bash
Warning  FailedKillPod  2m28s (x162 over 37m)  kubelet  error killing pod: failed to "KillPodSandbox" for "ee95c8..." with KillPodSandboxError: "rpcerror: code = Unknown desc = failed to destroy network for sandbox \"2a727b8...\": error getting ClusterInformation: connectionis unauthorized: Unauthorized"
```

## 調査

色々調査してみると、下記のような状況でした。

- 特定のnodeのみ発生
- どうやら移行対象のpodは移行先で元気にやっている
    - つまり、移行後の元pod削除に失敗している
- client-sideとあるので`~/.kube/cache`などクリアしてみたが解消せず
- マシンの再起動をしても解消せず
- 社内のVPNを切断しても解消せず
- Pod Distruption Budgetの予算使い切って一時的に待機しているわけでもなさそう
    - エラーの内容が明らかに違う
    - Deploymentのrunning pod countはrequiredを満たしている

## 対応

ひとまず移行先Podは元気に動いているということで、該当のPodを強制終了することにしました。

`kubectl delete pods <pod> --grace-period=0 --force`

これで削除したらdrainのstuckが解消され、無事node pool移行完了できました。

## 原因調査

軽く調査したんですがよくわかりませんでした。

[https://enumclass.tistory.com/262](https://enumclass.tistory.com/262)

→社内のSREに教えてもらった記事

[https://github.com/projectcalico/calico/issues/5712](https://github.com/projectcalico/calico/issues/5712)

→calico関連で見かけたissue

どちらもcalico起因かもっていうのはわかりましたが、そこまで時間無かったのと発生パターンが掴めなかったのであまり深追いしませんでした。

GKEでノード上げたりノード数変更したり色々やっていたのでそのあたりが関連したのかもしれませんが、特にpodが上がらなくなってアプリが死んだとか実害は無かったので。

## まとめ

結局、

- staging環境だった
- アプリが死んでなかった
    - evict先Podは生きていた
    - 他のPod間通信は問題無さそうだった

のでやむを得ずforce deleteしちゃいましたが、商用環境で、Podのcreateで起きたらどうしようと、少し不安になりました。

何か情報わかったら追記したいと思います。
