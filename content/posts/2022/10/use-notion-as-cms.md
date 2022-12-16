---
title: NotionをCMSとして使うためのアプリ実装
date: 2022-10-30
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


# Table of Contents


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


最後に配列に詰める際にisPageObjectReponse()で型ガードで確認しつつ型アサーションしてますが、`query()`の戻りの型が`(PartialPageObjestResponse | PageObjectResponse)[]`なので入れています。Partialの方は`type`と`id`しかpropertyが無いのですが、多分今回の叩き方だとそっちは対象データじゃ無さそうなので。


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


nodejsでGit関連の操作を行うために、今回はsimple-gitを使用しました。


[https://github.com/steveukx/git-js](https://github.com/steveukx/git-js)


マシン上のgitバイナリをラップしている形なのでgitで行いたい操作は一通り叩けます。下記はcloneしてremote branchのリストを取得している部分です。


```typescript
const git = simpleGit({
      baseDir: `${process.cwd()}/tmp`,
      binary: "git",
      maxConcurrentProcesses: 6,
      trimmed: false,
    });
// ...
try {
      await git.clone(config.github.repo, ".");
      const summary = await res._git.branch();
      res._branches = summary.all.filter((v) =>
        v.startsWith(res._branch_remote_prefix)
      );
    } catch (e) {
      throw e;
    }
```


差分を検知した場合はmdを上書き（または新規作成）して、画像ファイルも再配置しそれぞれ`add()`, `commit()`, `push()`しています。


### 差分検知


差分検知の流れは下記の通りです。

1. Notion APIからmdに変換（A）
2. 既存ファイルのmdを読み込み
3. 画像ファイルのパスを修正（UUID使用。後述）
4. 差分がある場合（A）でmdを上書き
5. 画像をnotionのS3からダウンロードし、これも再配置する

### 画像パスがS3の署名付きURLで毎回差分が出てしまう問題


Notion APIからmdに変換した直後のファイル（画像ファイル部分）はこんな感じになっています（文字列は適当に変更しています）。


あと、実装的に下記のコードも画像パスとして認識されてしまうので一部全角にしています…w


```markdown
！[](https://s3.us-west-2.amazonaws.com/secure.notion-static.com/5c8ecebd-9792-4eb1-9f9c-b9e65f359392/Untitled.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=HOGEHOGEus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20221030T102329Z&X-Amz-Expires=86400&X-Amz-Signature=hogehoge&X-Amz-SignedHeaders=host&response-content-disposition=filename%3D%22Untitled.png%22&x-id=GetObject)
```


Notionの仕様として、画像ファイルは全てS3にアップロードされ、アクセスには署名付きURLが必要になります。署名付きURLはAPIを叩く度に変更されますので、画像の変更が無くても差分が出てしまう問題が発生しました。


解決策としてはパスのUUIDで同一性を判定する方法があります。上記の例だと`5c8ecebd-9792-4eb1-9f9c-b9e65f359392`になります。


差分の確認を行う前にmdで下記のように置換を行います。


```markdown
# 変更前
！[](https://s3.us-west-2.amazonaws.com/secure.notion-static.com/5c8ecebd-9792-4eb1-9f9c-b9e65f359392/Untitled.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=HOGEHOGEus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20221030T102329Z&X-Amz-Expires=86400&X-Amz-Signature=hogehoge&X-Amz-SignedHeaders=host&response-content-disposition=filename%3D%22Untitled.png%22&x-id=GetObject)
# 変更後
！[5c8ecebd-9792-4eb1-9f9c-b9e65f359392.png](assets/images/notion/5c8ecebd-9792-4eb1-9f9c-b9e65f359392.png)
```


これだけだと画像の位置が変わっただけでもimageが再ダウンロードされてしまうので、Notion APIから取得した最新情報からUUIDのリストを取得しておき、それらが含まれるimageはそれぞれ削除しておきます。


```typescript
private deleteExistingImages(md: string, uuids: string[]): string {
    const lines = md.split(/\r?\n/);
    for (let [idx, line] of lines.entries()) {
      line = line.trim();
      if (!line.startsWith("![")) continue;

      let found = false;
      for (const uuid of uuids) {
        if (line.includes(uuid)) {
          found = true;
          break;
        }
      }
      if (found) {
        lines.splice(idx, 1);
      }
    }

    return lines.join("\n");
  }
```


そんな感じで

- 画像ファイルを毎回ダウンロードしなくて済む
- 画像ファイルが同じで位置が変わっただけでも無駄にダウンロードしない

を実現しました。


## Gitのcommit&pushからのPR作成


imageのダウンロードにはimage-downloaderを使わせていただきました。


[https://www.npmjs.com/package/image-downloader](https://www.npmjs.com/package/image-downloader)


ダウンロードまで完了したらcommit&pushします。


```typescript
await this._git.add(this.getMdPathForGit(page));
    await this._git.add(`${this.getImageDirForGit()}/*`);
    await this._git.commit(`update post ${page.permalink}`);
    await this._git.push(
      "origin",
      `${this._branch_local_prefix}${page.permalink}`,
      { "--set-upstream": null }
    );
```


最後に、PRを作成して終わりです。PRが既に存在する場合はスキップします。


```typescript
// create PR if not exists
    const pr = await this._github.rest.search.issuesAndPullRequests({
      q: `is:pr is:open "${this.getPRTitle(page)}"`,
    });
    if (pr.data.total_count === 0) {
      console.log("PR is not found, creating...");
      await this._github.rest.pulls.create({
        owner: this._github_user,
        repo: this._github_repo_name,
        head: `${this._github_user}:${this._branch_local_prefix}${page.permalink}`,
        base: "main",
        title: this.getPRTitle(page),
      });
      console.log("Done");
      return;
    }
    console.log("PR already exists");
```


# 実行場所


Notion APIにweb hook的な機能が無いみたいなのでこちらから取りに行く必要があります。が、記事を書くのは自分しかいないので、記事を書いて公開したいときに任意に実行できる　で良いかと思っています。


今のところGithub Actionsで実行できるようにしてみようと思います。

