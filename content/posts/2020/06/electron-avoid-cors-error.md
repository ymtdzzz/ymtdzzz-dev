---
title: "Electron の CORS ブロックを回避する方法について"
date: 2020-06-06
tags:
  - "electron"
  - "react"
  - "typescript"
  - "CORS"
published: True
category: Programming
---

## Electron で CORS エラー

Electron の Render プロセスでクロスオリジンのリクエストを投げた際、通常の Web と同様 CORS エラーでブロックされます。通信先が自前の API サーバだったりした場合にはそちらの設定で`Access-Control-Allow-Origin`を許可すれば OK です。

この制約はセキュリティ上必要なものですが、どうしてもクロスオリジンのリクエストを投げたい場合もあるかと思います。私の場合は、ある markdow エディタに、貼り付けた URL から自動的にページのタイトルを fetch して挿入する機能を実装するときに遭遇しました。

<!--more-->

解決方法は下記の通りです。

1. クロスオリジンの fetch を行うプロキシサーバを構築し、Electron からの fetch 先を集約する
2. `new BrowserWindow`のパラメータ`webPreferences`の`webSecurity`を`false`にする
3. Electron の IpcEvent を使用し、fetch だけ Main process(nodejs)でやってもらう

1 はプロキシサーバの運用コストが発生するので、そのあたりペイできそうなら採用するのもアリです。

2 はセキュリティリスクが増大するのであまりよろしくないかと思います。

今回は 3 を採用してみました。

## IpcEvent で Main process に処理をしてもらう

![処理フロー](../../../../gridsome-flex-markdown-starter/src/assets/images/old/images/20200610/image.png)

Electron の IpcEvent を使うことで、Render process から任意のタイミングで Main  process の関数を call することができます。

### Main process 側のイベント設定

Main process 側でイベントハンドラを設定しておきます。イベント名については、Main 側を"fetch-url-request"、Render 側を"fetch-url-response"としました。

記載するファイルは`new BrowserWindow`している`index.ts`とか`main.ts`とかで OK です。

```js
import fetch from 'node-fetch'
import { ipcMain } from 'electron'

// Render から発火されるイベント
ipcMain.on('fetch-url-request', async (event, url) => {
    const res = await fetch(url)
    // body テキストを取得
    const body = await res.text()
    // Render のイベントを発火してデータ受け渡し
    event.sender.send('fetch-url-response', body)
})
```

### Render process 側のイベント設定

Render 起点なので、ここでは例として"onPaste"関数で呼び出す体でいきます。

```js
// React のプロジェクトで import { ipcRenderer } from 'electron'すると、'fs.existsSync is not a function'になるので、その対策。
// https://github.com/electron/electron/issues/9920
const ipcRenderer = window.require('electron').ipcRenderer

const onPaste = (pastedText: string) => {
    ipcRenderer.send('fetch-url-request', pastedText)
}

ipcRenderer.on('fetch-url-response', (_, res) => {
    console.log(`bodyis: ${res}`)
})
```

## 注意点

Main process で生成した Response をそのまま Render process に送ることはできません。そのまま Response オブジェクトを送信しても、nodejs native オブジェクトのため Render 側ではハンドルできません。

そのため、受け渡し可能な型に変換して送信する必要があります。例えば今回の場合は、text()で Body の string を返すようにしています。

Response の特定のデータだけほしいとか、Response を解析してその結果だけ返したいとかの場合に使える方法かと思います。
