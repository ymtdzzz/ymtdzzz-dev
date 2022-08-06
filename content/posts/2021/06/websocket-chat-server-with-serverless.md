---
title: "Typescriptを使用したサーバレスWebsocketチャットサーバーの構築"
date: 2021-06-06
tags:
  - "Typescript"
  - "Lambda"
  - "AWS"
  - "Websocket"
  - "React"
published: True
category: Infrastructure
---

チャットサーバーの見積もり相談で、Websocket使った場合の実装を整理したので、メモっておきます。

<!--more-->


## 動作確認 {#動作確認}

以下のURLで動作確認できます。

<https://reactplayground.zeroclock.dev/WebsocketChat>

-   複数タブで開く
    ![](/images/old/ox-hugo/2021-06-06_21-18.png)

-   Sign Upでユーザ登録＆ログイン
    ![](/images/old/ox-hugo/2021-06-06_21-20.png)

-   お互いのIDを教え合う
    ![](/images/old/ox-hugo/2021-06-06_21-23.png)

-   チャットする
    ![](/images/old/ox-hugo/2021-06-06_21-24.png)

-   片方が切断すれば、きちんとステータスも変わります
    ![](/images/old/ox-hugo/2021-06-06_21-25.png)

上記以外にも、切断後に再度ログインして相手IDを入力して再接続すると、過去のメッセージもきちんと再現してくれます（メッセージ情報の永続化）。


## 構成図 {#構成図}

今回は、サーバレス（Lambda）でチャットサーバーを構築することを検討してみました。

![](/images/old/ox-hugo/06-06-overview.svg)

API GatewayがWebsocketのフロントエンドとして機能し、リクエストに応じて各バックエンド(handlers)にリクエストを流します。


## 処理フロー {#処理フロー}

ちょっと図だとわかりにくいので、Websocketに絞った処理の流れを下記に示します。

> -   [Client -> Server] Websocket通信確立リクエスト送信（with アクセストークン）
> -   [Server] `Authorizer` においてトークンの検証処理実行
> -   [Client <- Server] 200 OK
> -   [Client -> Server] `$connect` request
> -   [Server] `handleSocketConnect` において、DynamoDBに接続情報を登録し、通信相手がすでにONLINEの場合は、ステータス更新情報を **WebSocket経由で** 送信
> -   [Client <- Server] 200 OK
> -   [Client -> Server] `GETMSG` request
> -   [Server] `getMsg` において、DynamoDBから該当するconnectionに紐づくメッセージ情報を取得し、 **WebSocket経由で** 送信
> -   [Client <- Server] 200 OK
> -   ...

Websocketはイベント駆動なので、 `GETMSG` のリクエストを送信しても、 **そのレスポンスとしてメッセージ情報が返却されるわけではない** ことに注意が必要です。

返却情報については、ClientからServerに送信したのと同じように、ServerからClientに対して `GETMSG` イベント（異なるイベントの可能性も有り）としてリクエストが飛んでくるので、それをClient側でハンドリングすることで取得します。

よって、例としてメッセージ配信後に相手が接続を切った場合の処理フローは下記のようになります。

![](/images/old/ox-hugo/06-06-overview2.svg)


## 実装 {#実装}

ソースは下記にあります。

-   バックエンド：<https://github.com/zeroclock/websocket-chat-server>
-   フロントエンド：<https://github.com/zeroclock/react-playground/tree/master/src/components/websocket%5Fchat>

バックエンドとフロントエンドのうち、メッセージ送信に関連する処理をピックアップして解説します（AuthorizerやCognito連携周りの実装については省略）。

なお、今回はFE、BEどちらもTypescriptで実装しました。


### （Alice）フロントエンド（SENDMSGイベントの発火処理） {#alice-フロントエンド-sendmsgイベントの発火処理}

<https://github.com/zeroclock/react-playground/blob/master/src/components/websocket%5Fchat/Chat.tsx>

```typescript
const onSendMsg = () => {
  if (connection) {
    const data = {
      action: 'SENDMSG',
      message,
      timestamp: new Date().getTime(),
      fromSub: props.loginInfo.id,
      toSub: partnerId,
    }
    connection.send(JSON.stringify(data))
    const msg: Message = {
      message: data.message,
      fromSub: data.fromSub,
      toSub: data.toSub,
      timestamp: new Date(data.timestamp),
    }
    addMsg(msg)
  }
}
```

<div class="src-block-caption">
  <span class="src-block-number">Code 1</span>:
  フロントエンドのSENDMSGイベントの発火処理の実装
</div>

まず、メッセージを送信するにはフロント起点でイベントを送信しないといけません。

とはいえ、やることとしては、予め確立しておいたWebsocket接続（ `connection` ）の `send()` を呼び出すだけです。


### バックエンド（sendMessage） {#バックエンド-sendmessage}

<https://github.com/zeroclock/websocket-chat-server/blob/master/src/controllers/sendmsg.controller.ts>

```typescript
export const sendmsg: APIGatewayProxyHandler = async (event, _context) => {
  try {
    //const connectionId = event.requestContext.connectionId;
    const data = JSON.parse(event.body);

    const message = data['message'];
    const timestamp = data['timestamp'];
    const fromSub = data['fromSub'];
    const toSub = data['toSub'];

    const messageId = await dynamodbconnector.registerMessage(message, fromSub, toSub, timestamp);
    // send Message to partner user
    const sockets = await dynamodbconnector.findSocketsBySub(toSub);
    if (sockets.Count > 0) {
      const sendMessage: SocketMessage = {
        action: 'SENDMSG',
        message,
        fromSub,
        toSub,
        timestamp,
      };
      await apigatewayconnector.generateSocketMessage(
        sockets.Items[0].connectionId,
        JSON.stringify(sendMessage),
      );
    }

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'text/plain',
        'Access-Control-Allow-Origin': CONSTANTS.CORS_ORIGIN,
      },
      body: 'Greeting delivered',
    };
  } catch (e) {
    console.error('Failed to store message and send message to partner user', e);
    return {
      statusCode: 500,
      headers: {
        'Content-Type': 'text/plain',
        'Access-Control-Allow-Origin': CONSTANTS.CORS_ORIGIN,
      },
      body: 'Failed to store message and send message to partner user',
    };
  }
}
```

<div class="src-block-caption">
  <span class="src-block-number">Code 2</span>:
  バックエンドのSENDMSGイベントの処理
</div>

フロント側からSENDMSGイベントが送信されましたので、バックエンドではsendMsgハンドラが呼び出されます。

なお、途中で出てくる `hogeconnector` については、aws-sdkをラップした関数です。

まず、取得したイベントデータから下記の情報を取り出し、DynamoDBにメッセージ情報を登録します。

-   message: メッセージ本文
-   timestamp: 送信日時のタイムスタンプ
-   fromSub: 送信元ID
-   toSub: 送信先ID

続いて、送信先IDを元に送信先の `connectionID` を取得（ `dynamodbconnector.findSocketsBySub()` ）し、SENDMSGイベントを送信します（ `apigatewayconnector.generateSocketMessage()` ）。


### （Bob）フロントエンド（SENDMSGイベントのハンドリング） {#bob-フロントエンド-sendmsgイベントのハンドリング}

<https://github.com/zeroclock/react-playground/blob/master/src/components/websocket%5Fchat/Chat.tsx>

```typescript
const initializeConnection = (c: WebSocket) => {
  c.onopen = WSOnOpen
  c.onclose = WSOnClose
  c.onerror = WSOnError
  c.onmessage = WSOnMessage
  setConnection(c)
}
// ...
const WSOnMessage = (event: MessageEvent<any>) => {
  console.log('onMessage')
  // handle incoming message
  const data = JSON.parse(event.data)
  console.log(JSON.stringify(data))
  switch (data['action']) {
    case 'ISONLINE':
      // ...
    case 'SENDMSG':
      console.log('received message')
      console.log(`timestamp: ${data['timestamp']}`)
      const msg: Message = {
        message: data['message'],
        fromSub: data['fromSub'],
        toSub: data['toSub'],
        timestamp: new Date(data['timestamp']),
      }
      addMsg(msg)
      break
      // ...
      break
  }
}
```

<div class="src-block-caption">
  <span class="src-block-number">Code 3</span>:
  フロントエンドのSENDMSGイベントのハンドリング処理の実装
</div>

Server側から送信されたSENDMSGイベントをハンドリングするには、 `MessageEvent` を引数とする関数を定義し、Websocketインスタンスの `onmessage` に登録します。

actionによって処理を分岐させることで様々な種類のイベントをハンドリングすることが可能になります。

SENDMSGイベントについては、取得した情報（メッセージ本文、timestamp等）を単にstateに保存するだけのシンプルな処理になります。


## インフラの構築 {#インフラの構築}

インフラについてはServerless frameworkを使用してデプロイします。

<https://github.com/zeroclock/websocket-chat-server/blob/master/serverless.ts>

詳細は上記ソースファイルをご参照ください。

やってることとしては、API GWの設定、DynamoDBのテーブル作成、Lambda関数の実行ロール作成、CognioUserプールの作成等です。


## さいごに {#さいごに}

API GatewayでWebsocketが対応したおかげで、かなり低コストでP2P通信が実現できることがわかって良かったです。

サーバレスは従量課金なので、個人学習の強い味方。（EC2をプライベートサブネットに立ててNATGWのコストにビビる人は多いハズ）

チャットとか、バックエンドの状況をできるだけリアルタイムにフロントに反映したい場合には重宝する技術ではありますが、注意も必要です。

タブ開きっぱとかでコネクション張りっぱなしだとバックエンドの負荷が高まるため、一定時間操作が無かったら切断して、画面に戻ってきたら再接続するとか、しっかり使うのには色々やらないといけないことや考えないといけないことが多い技術かと思います。

ajar（一定時間ごとにリクエスト投げて新規メッセージ等を確認する）なども検討すべきですね。
