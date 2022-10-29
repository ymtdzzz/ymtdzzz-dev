---
title: NotionをCMSとして使うためのアプリ実装
date: 2022-10-29
tags:
 - Notion
 - Typescript
 - markdown
 - github
published: true
category: Programming
---

先日、Notionから自動的に自ブログの記事更新分を自動commit&pushしてpull requestを作成してくれるツールを作りました。


[https://github.com/ymtdzzz/notion-blog-converter](https://github.com/ymtdzzz/notion-blog-converter)


主に使用した技術スタックとしては下記の通り。

- nodejs
- typescript
- Github API
- Notion API

使い方とかは別で記事にしようと思っているので、ここでは主に実装にフォーカスした内容を書きます。


# 全体の流れ


全体の流れはこちら。


![28fb7d7f-1acf-4a22-a273-adc29671661f.png](../../../../gridsome-theme/src/assets/images/notion/28fb7d7f-1acf-4a22-a273-adc29671661f.png)


主な関心事はこの辺。

- Notion APIからの記事情報取得とmarkdownへの変換
- Notionから取得した記事と既存リポジトリとの差分確認
- Gitのcommit&pushからのPR作成
- 実行場所

# 実装


言語については、Notion APIからmarkdownに変換してくれるライブラリが [notion-to-md](https://github.com/souvikinator/notion-to-md) （nodejs製）ほぼ一択だったので自動的にnodejs（typescript）になりました。


ほんとはシングルバイナリでポータビリティ重視でGoとかRustあたりで考えてたんですがしょうがない。ポータビリティについてはコンテナ化するとか方法もあるので（と言いつつ普通にホストマシンで実装しちゃいましたが・・・）。


先述した技術的な関心事をどんな感じで実装したかをコード抜粋しつつ記載していきます。


## Notion APIからの記事情報取得とmarkdownへの変換


### 記事情報取得


Notion APIに公式クライアントがあるのでありがたく使わせてもらいます。


[https://github.com/makenotion/notion-sdk-js](https://github.com/makenotion/notion-sdk-js)


初期化方法などについては公式ドキュメントを見ていただくとして、記事情報取得部分について。


```typescript
		do {
        const res: QueryDatabaseResponse = await this.client.databases.query({
          database_id: database_id,
          start_cursor: cursor,
          filter: {
            and: [
              {
                property: this._config.props.exclude_checkbox,
                checkbox: {
                  equals: false,
                },
              },
              {
                property: this._config.props.include_checkbox,
                checkbox: {
                  equals: true,
                },
              },
            ],
          },
        });

        has_more = res.has_more;
        cursor = res.next_cursor !== null ? res.next_cursor : undefined;
        posts = posts.concat(
          res.results.filter((v) =>
            this.isPageObjectResponse(v)
          ) as PageObjectResponse[]
        );
      } while (has_more);
```


ページネーションの概念があるので`do-while`で全部回します。メモリ的な部分は記事の数がやばいことになってから考えます。


`query()`の結果に`has_more`があるので、それが`true`の間記事を取得し続ける感じです。また、`next_cursor`で毎回取得位置を設定しています。


最後に配列に詰める際にisPageObjectReponse()で型ガードで確認しつつ型アサーションしてますが、`query()`の戻りの型が`(PartialPageObjestResponse | PageObjectResponse)[]`なので入れています。Partialの方は`type`と`id`しかpropertyが無いのですが、多分今回の叩き型だとそっちは対象データじゃ無さそうなので。


### markdownへの変換


記事情報をmarkdownに変換するのは自前でやろうとすると結構大変で、blockを再帰的にAPIを叩いて取得しつつ、`type`（textとかlinkとか）毎に正しいmarkdownに置き換えていく必要があります。


今回は [notion-to-md](https://github.com/souvikinator/notion-to-md) でやってくれるのでサクッといけました。


```typescript
const nclient = new Client({
  auth: config.notion.token,
  logLevel: LogLevel.DEBUG,
});
// ...
const n2m = new NotionToMarkdown({ notionClient: nclient });
// ...
for (const page of pages) {
      const mdblocks = await n2m.pageToMarkdown(page.id);
      const mdString = n2m.toMarkdownString(mdblocks);
// ...
```


## Notionから取得した記事と既存リポジトリとの差分確認


### Git関連の操作


### 画像パスがS3の署名付きURLで毎回差分が出てしまう問題


## Gitのcommit&pushからのPR作成


TBD


# 実行場所

