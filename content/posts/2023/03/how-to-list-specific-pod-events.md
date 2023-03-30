---
title: 特定Podのeventをリストアップするコマンド
date: 2023-03-30
tags:
 - Kubernetes
 - snippet
published: true
category: Infrastructure
---

K8s podがdeleteされるときにReadiness probeが失敗する事象を調査していて、特定のpodのeventをリストアップする方法を探すのに少し手間取ったのでメモしておきます。


```text
kubectl get events --sort-by .lastTimestamp --field-selector involvedObject.name={your-pod-name}
```


なお、ソートやフィルタリング条件を変えたい場合は、`kubectl get events -o json`でどんな構造でフィールド指定すれば良いか確認することができます。


直近イベント出てないとかで見つからない場合はエラーになります（それはそう）


```text
No resources found in default namespace.
```


# 参考

- [https://stackoverflow.com/questions/40636021/how-to-list-kubernetes-recently-deleted-pods](https://stackoverflow.com/questions/40636021/how-to-list-kubernetes-recently-deleted-pods)
- [https://zaki-hmkc.hatenablog.com/entry/2020/03/28/085938](https://zaki-hmkc.hatenablog.com/entry/2020/03/28/085938)
