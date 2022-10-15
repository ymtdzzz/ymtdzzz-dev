---
title: "Kittyでscrollback bufferが折り返されて上手くコピペできない場合の対処法"
date: 2022-08-09
tags:
  - "fish"
  - "kitty"
  - "vim"
published: true
category: Tool
---

最近Kitty + fishの組み合わせでshellを運用しています。

[https://sw.kovidgoyal.net/kitty/](https://sw.kovidgoyal.net/kitty/)

[https://fishshell.com/](https://fishshell.com/)

- Kittyのscrollback buffersが便利
    - terminal組み込みではなくいつものエディタ（vim）が使える安心感
- fishの自動補完やhistoryのfzfによるスムーズな検索

と、非常に気に入っているのですが、一点気になる点として、shell上の表示が折り返されている部分もそのままscrollback buffersに渡されてしまうため、作業ログなどを保存する際に苦労することがあることがあげられます。

## 例

例えば、色々分割して狭くなったbuffer上でk8sのpodの詳細を取得してログとして残しておきたいとします（`k describe pod <pod_name>`）。

すると、shell上だと下記のように折り返して表示されます。

![scrollback_01.png](../../../../gridsome-theme/src/assets/images/2022/08/scrollback_01.png)

ここまでは想定通りですが、このscreenback bufferをvimで開いてみます（デフォルトなら`Cmd+h`）。

![scrollback_02.png](../../../../gridsome-theme/src/assets/images/2022/08/scrollback_02.png)

画面上の改行も含めてまるっとvimに渡されてしまっています。エディタに渡された時点ですでにこうなっているので、`set nowrap`とか行番号を消しても無意味です。

実際にこれをコピペしてみると下記のようになります。

```bash
ry volume)
    Path:          /etc/ssl/certs
    HostPathType:  DirectoryOrCreate
  etc-ca-certificates:
    Type:          HostPath (bare host dir
ecto
ry volume)
    Path:          /etc/ca-certificates
    HostPathType:  DirectoryOrCreate
  k8s-certs:
    Type:          HostPath (bare host dir
ecto
ry volume)
    Path:          /var/lib/minikube/certs
    HostPathType:  DirectoryOrCreate
  usr-local-share-ca-certificates:
    Type:          HostPath (bare host dir
ecto
ry volume)
    Path:          /usr/local/share/ca-cer
tifi
cates
    HostPathType:  DirectoryOrCreate
  usr-share-ca-certificates:
    Type:          HostPath (bare host dir
ecto
ry volume)
    Path:          /usr/share/ca-certifica
tes
    HostPathType:  DirectoryOrCreate
QoS Class:         Burstable
Node-Selectors:    <none>
Tolerations:       :NoExecute op=Exists
Events:            <none>
```

 色々改行されて壊れちゃっています。

## 解決策

こういう場合は文字サイズを小さくして収まるようにしてからscreenback buffersを開き、文字サイズを戻すことで解消できます。

1. コマンド実行後、文字サイズを小さくする（`Cmd+’-’`）
2. screenback buffersを開く（`Cmd+h`）
3. 文字サイズを元に戻す（`Cmd+’+’`）

すると、エディタ上ではちゃんとwrapが効いているがきちんと一行として表示されてくれます。

![scrollback_03.png](../../../../gridsome-theme/src/assets/images/2022/08/scrollback_03.png)

コピペしても想定通りの形になります。

```bash
Volumes:
  ca-certs:
    Type:          HostPath (bare host directory volume)
    Path:          /etc/ssl/certs
    HostPathType:  DirectoryOrCreate
  etc-ca-certificates:
    Type:          HostPath (bare host directory volume)
    Path:          /etc/ca-certificates
    HostPathType:  DirectoryOrCreate
  k8s-certs:
    Type:          HostPath (bare host directory volume)
    Path:          /var/lib/minikube/certs
    HostPathType:  DirectoryOrCreate
  usr-local-share-ca-certificates:
    Type:          HostPath (bare host directory volume)
    Path:          /usr/local/share/ca-certificates
    HostPathType:  DirectoryOrCreate
  usr-share-ca-certificates:
    Type:          HostPath (bare host directory volume)
    Path:          /usr/share/ca-certificates
    HostPathType:  DirectoryOrCreate
QoS Class:         Burstable
Node-Selectors:    <none>
Tolerations:       :NoExecute op=Exists
Events:            <none>
```

## まとめ

根本解決にはならないですが、ショートカットキーで一瞬で文字サイズ変更できるので都度やってもそこまで面倒では無く、今のところはこれでストレス無く（全く無いわけではないけど）運用できています。
