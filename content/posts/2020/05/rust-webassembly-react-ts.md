---
title: "Rust で Webassembly を書いて、Typescript で React を書くための環境構築"
date: 2020-05-28
tags:
  - "rust"
  - "webassembly"
  - "react"
  - "typescript"
  - "webpack"
published: True
category: Programming
---

## 前提
この記事では、Rust(cargo)と npm は導入済みを前提としています。
知識的には[Rust の公式 WebAssembly チュートリアル](https://rustwasm.github.io/docs/book/)を一通り読んだくらいで、今回は Wasm と React どう組み合わせるのよってところを重点的に。

<!--more-->

## 必要なモジュール、コマンドの準備
- wasm-pack

  [wasm-pack のホームページ](https://rustwasm.github.io/wasm-pack/installer/)を参考にして導入。

- cargo-generate

  今回はこの cli ツールで、Rust で WebAssembly の雛形を作成したいと思います。

  ```sh
  $ cargo install cargo-generate
  ```
  
- wasm32-unknown-unknown ターゲットアーキテクチャ

  ```sh
  $ rustup target add wasm32-unknown-unknown
  ```

## WebAssembly プロジェクト作成
※この辺りの手順は基本的に上記の公式チュートリアルとほぼ同じ内容です。

まず、git からテンプレートを引っ張ってきます。

プロジェクト名は適当に設定します。

```sh
$ cargo generate --git https://github.com/rustwasm/wasm-pack-template
🤷  Project Name: wasm-react-tutorial
🔧  Creating project called `wasm-react-tutorial`...
✨  Done! New project created /Users/yourname/repos/wasm-react-tutorial

$ wasm-react-tutorial
```

一応、`wasm-pack`コマンドで wasm の生成とそれをラップする js ファイル一式が正常に生成されることを確認しておきます。

```sh
$ wasm-pack build
```

`npm init`で、wasm-react-tutorial フォルダ内にフロントエンド部分の雛形を作成します。

```sh
$ npm init wasm-app www
```

一旦ここまでを終えると、下記のようなディレクトリ構成になっているはずです（一部省略）。

```
wasm-react-tutorial/
├── Cargo.lock
├── Cargo.toml
├── LICENSE_APACHE
├── LICENSE_MIT
├── README.md
...
├── pkg
└── www
    ├── LICENSE-APACHE
    ├── LICENSE-MIT
    ├── README.md
    ├── bootstrap.js
    ├── index.html
    ├── index.js
    ├── package-lock.json
    ├── package.json
    └── webpack.config.js
```

www ディレクトリ内で`npm install`して必要なパッケージをインストールしつつ、wasm-pack で生成された pkg ディレクトリについても依存ライブラリとして使用する設定を行います。

```sh
# www ディレクトリ内
$ npm install

# www/package.json に下記の記述を追加
  "dependencies": {
    ...
    "wasm-react-tutorial": "file:../pkg"

# もう一回 npm i
$ npm i
```

最後に、www/index.js の import を修正します。

```js
import * as wasm from "wasm-react-tutorial";
```

サーバを立ててみて、正常に動作することを確認します。

```sh
$ npm run start
# localhost:8080 にアクセスすると、「Hello, wasm-react-tutorial!」というアラートが表示されます。
```

## React と typescript の環境を整える
さて、ここからが本番です。

**これ以降の作業ディレクトリは www です。**

webpack は既に導入済みなので、まずは typescript を入れます。

```sh
$ npm i -D typescript ts-loader
```

www/tsconfig.json を作成し、一旦下記のように設定しておきます。

```json
{
  "compilerOptions": {
    "sourceMap": true,
    "baseUrl": "./",
    "target": "es5",
    "module": "esNext",
    "lib": ["es2018", "dom"],
    "jsx": "react",
    "strict": true,
    "rootDirs": [
      "src"
    ],
    "types": [
      "react"
    ],
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "moduleResolution": "Node",
    "typeRoots": ["types", "node_modules/@types"]
  },
  "include": [
    "src"
  ],
  "exclude": [
    "node_modules"
  ]
}
```

react を入れます。

```sh
$ npm i -S react react-dom @types/react @types/react-dom
```

www/src ディレクトリを作り、必要なファイルを作成しつつ、不要な www 直下の index.js を削除します。

```sh
$ mkdir src/bootstrap.tsx
$ touch src/index.tsx
$ touch src/App.tsx
$ touch src/index.html
$ rm index.js
$ rm bootstrap.js
$ rm index.html
```

src/index.html は下記の通り。

```html
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>wasm-react-tutorial</title>
</head>
<body>
  <div id="root"></div>
</body>
</html>
```

src/bootstrap.tsx は下記の通り。

```jsx
// エントリーポイント。wasm を import するモジュールは非同期で import する必要があるので、
// こうすることで、ソース内のどこでも wasm を import することができるようになる。
import("./index").catch(e => console.error("Error importing `bundle.js`:", e));
```

src/index.tsx は下記の通り。

```jsx
import React from "react";
import ReactDOM from "react-dom";
import App from "./App";

ReactDOM.render(<App />, document.getElementById("root"));
```

src/App.tsx は下記の通り。

```jsx
import React from "react";

const App = () => {
  return (
    <div>wasm-react-test</div>
  );
};

export default App;
```

続いて、webpack で html もビルドできるようにする`html-webpack-plugin`をインストールします。

```sh
$ npm i -D html-webpack-plugin
```

最後に、webpack.config.js を設定します。

```js
const path = require('path');
const htmlWebpackPlugin = require("html-webpack-plugin");

module.exports = {
  entry: path.resolve(__dirname, "src/bootstrap.tsx"),
  output: {
    path: path.resolve(__dirname, "public"),
    filename: "bootstrap.js"
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        loader: "ts-loader"
      },
    ]
  },
  resolve: {
    extensions: [".ts", ".tsx", ".js"]
  },
  devServer: {
    contentBase: path.resolve(__dirname, "public")
  },
  plugins: [
    new htmlWebpackPlugin({ template: './src/index.html' }),
  ]
};
```

## 動作確認

まずは wasm 呼び出さずに普通にビルドして dev-server を立ててみます。

```sh
# www にて実行
$ npm run start
```

![wasm 無しバージョン](../../../../gridsome-flex-markdown-starter/src/assets/images/old/images/20200528/wasm-react-tutorial-no-wasm.png)

続いて、wasm の greet()メソッドを読んでみます。

```jsx
// src/App.tsx
import React from "react";
import * as wasm from "wasm-react-tutorial";

const App = () => {
  wasm.greet();
  return (
    <div>wasm-react-test</div>
  );
};

export default App;
```

![wasm 呼び出してみる](../../../../gridsome-flex-markdown-starter/src/assets/images/old/images/20200528/wasm-react-tutorial.png)

これで自由に React アプリから wasm を import できるようになりました！
