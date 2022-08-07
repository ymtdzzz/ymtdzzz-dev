---
title: "【Typescript】axiosのレスポンスはきちんと型チェックしよう"
date: 2020-08-12
tags:
  - "typescript"
  - "axios"
published: True
category: Programming
---

## Axiosでエラー {#axiosでエラー}

Axiosで外部APIを叩いてデータを取得したいと思い、下記のコードを書いたとします。

<!--more-->

```typescript
import axios, { AxiosPromise } from "axios";

interface CatApiResponse {
  name: string;
  age: number;
  parents: string[];
}

const client = axios.create({
  baseURL: "https://example.com/api/v2/",
  headers: {
    "Content-Type": "application/json"
  }
});

const fetchAllCat = (): AxiosPromise<CatApiResponse> => client.get("cat");

const hoge = () => {
  const data = fetchAllCat();
  data.then((data) => {
    data.data.parents.map((parent) => {
      console.log(parent);
      return "hoge";
    });
  });
};
```

<div class="src-block-caption">
  <span class="src-block-number">Code 1</span>:
  AxiosでAPIを叩いて情報を取得するコード例
</div>

IDEで型推定を確認すると、確かに `CatApiResponse` になっている。

![](../../../../gridsome-flex-markdown-starter/src/assets/images/old/ox-hugo/20200812_175551.png)

けど、実際はnullかもしれないし、 `CatApiResponse` のinterfaceに則したデータ構造じゃないかもしれない。で、実際に変なデータを返すAPIを用意して実行すると、案の定 `data.data.parents.map()` のところでコケる。でも、IDEにも怒られないし、コンパイル時にもツッコまれない。


## カスタム型ガードでちゃんとチェックする {#カスタム型ガードでちゃんとチェックする}

イマイチ釈然としないけど、型ガードでちゃんとデータをチェックしてから返却しよう　というお話。

```typescript
const isCatApiResnpose = (arg: any): arg is CatApiResponse => {
  return (arg.name !== undefined
    && arg.age !== undefined
    && arg.parents !== undefined
    && Array.isArray(arg.parents))
}
```

<div class="src-block-caption">
  <span class="src-block-number">Code 2</span>:
  CatApiResponseの型ガード例
</div>

こんな感じの型ガードを書いてあげて、 `fetchAllCat()` で受け取ったPromiseをresolveしたときに、きちんとデータがCapApiResponseのinterfaceに準拠していることを確認してあげる必要がある。

```typescript
const hoge = () => {
  const data = fetchAllCat();
  data.then((data) => {
    if (isCatApiResnpose(data.data)) {
      data.data.parents.map((parent) => {
        console.log(parent);
        return "hoge";
      });
    }
  });
};
```

<div class="src-block-caption">
  <span class="src-block-number">Code 3</span>:
  きちんと型チェックを行う例
</div>

こうすることで、はちゃめちゃなデータが返ってきても安全に処理ができる（これでいいのか...?）。

実際はReactでデータをstateにsetしたりすることもあるが、その際はnullとか想定外のデータ構造だった場合は空のCatApiResponseを準備して返して上げれば単なる「データ無し」として扱える。

で、ここで面倒なのが、「空のhoge interfaceのデータ」を作ることで、構造が複雑だと一々手動でemptyHogeDataみたいなものを作らないといけない。ただ、その場合は該当するinterfaceを実装したclassを作っちゃって、そのconstructorで空を作らせるのも手かな　と。

ということで、今回はtypescriptのお話でございました。
