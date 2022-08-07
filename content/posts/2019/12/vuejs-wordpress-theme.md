---
title: "SPA（Vuejs）でwordpressテーマを作成した"
date: 2019-12-18
tags:
  - "PHP"
  - "Vuejs"
  - "webpack"
  - "Wordpress"
published: True
category: Programming
---
## Vue.jsでwordpressテーマ作成

2019/12/16に、このブログのテーマをリニューアルした。

今回はSPAに挑戦したかったので、Vue.jsを採用してだいたい２週間ほどで完成までこぎつけることができた。

<!--more-->

WordpressをAPIとしてのみ使用し、完全に独立したSPAサイトを作成する例はいくつか見られたが、「wordpressテーマ」としてSPAを活用した例はあまり見られない（一応あるにはあったが、細かい実装部分についてはあまり情報がなかった）ため、記事にしようと考えた。 

## パフォーマンス

まずは現状のパフォーマンスその他ベンチマーク結果について簡単に紹介しておく。 

  * Google Insights

![](../../../../gridsome-flex-markdown-starter/src/assets/images/old/wordpress/bd42ca71-800x232.png)

  * Google Lighthouse

![](../../../../gridsome-flex-markdown-starter/src/assets/images/old/wordpress/7f2659a1-800x234.png)

  * Google モバイルフレンドリーテスト   

![](../../../../gridsome-flex-markdown-starter/src/assets/images/old/wordpress/a69beede-800x713.png)

アクセシビリティは86だったが、基盤的な所で修正が必要な項目は特になかったので、ちょこちょこした所を修正して90台には載せたいと思う。 

SPAで課題となるパフォーマンス（＝初期表示）、SEO対策については特に問題無さそうだったのでひとまず安心。ただ、SEOについてはこれから運用してみないとわからないので、しばらく様子を見守っていく。 

## SPAテーマの作成

このテーマ作成にあたり、EvanAgee氏の

[GitHub &#8211; EvanAgee/vuejs-wordpress-theme-starter: A WordPress theme with the guts ripped out and replaced with Vue][1]を参考にしている。 

フォルダ構成やWebpack.config.js、導入パッケージについては上記リポジトリを一旦真似してみて、不要なものやバージョン見直しなどを行っている。 

### 導入パッケージ package.json 

```json
{
...
  "devDependencies": {
    "@babel/core": "^7.7.4",
    "@babel/plugin-proposal-object-rest-spread": "^7.7.4",
    "@babel/polyfill": "^7.7.0",
    "@babel/preset-env": "^7.7.4",
    "@fortawesome/fontawesome-svg-core": "^1.2.25",
    "@fortawesome/free-brands-svg-icons": "^5.11.2",
    "@fortawesome/free-solid-svg-icons": "^5.11.2",
    "@fortawesome/vue-fontawesome": "^0.1.8",
    "axios": "^0.19.0",
    "babel-loader": "^8.0.6",
    "cross-env": "^6.0.3",
    "css-loader": "^3.2.0",
    "dayjs": "^1.8.17",
    "extract-text-webpack-plugin": "^4.0.0-beta.0",
    "file-loader": "^5.0.2",
    "highlight.js": "^9.17.1",
    "lodash": "^4.17.15",
    "node-sass": "^4.13.0",
    "normalize.css": "^8.0.1",
    "reset-css": "^5.0.1",
    "sass-loader": "^8.0.0",
    "style-loader": "^1.0.0",
    "uglifyjs-webpack-plugin": "^2.2.0",
    "url-loader": "^3.0.0",
    "vue-carousel": "^0.18.0",
    "vue-lazyload": "^1.3.3",
    "vue-loader": "^15.7.2",
    "vue-router": "^3.1.3",
    "vue-session": "^1.0.0",
    "vue-template-compiler": "^2.6.10",
    "vuex": "^3.1.2",
    "vuex-persistedstate": "^2.7.0",
    "webpack": "^4.41.2",
    "webpack-bundle-analyzer": "^3.6.0",
    "webpack-cli": "^3.3.10",
    "webpack-dev-server": "^3.9.0"
  },
  "dependencies": {
    "vue": "^2.6.10"
  }
}
```

#### dayjs

日付系のライブラリ。最初はmomentjsを使用していたが、いざビルドすると結構な容量があった＆localeは基本的に日本だけなので、軽量ライブラリのdayjsで代用することにした。

全て実装が完了してからの修正となったが、そこまで記述方法に差があるわけではないので、momentでgrepしてちまちま直した。 

#### lodash

実装のほとんどがAPIのレスポンスをあれこれする処理だったので、こういう便利系ライブラリを使うことになった。 ただ、やはりこれも全部入りだと容量がでかいので、一部分だけimportして使用している。 

#### highlightjs

これも、単純にimportするだけだとサポートしている全言語の内容を持ってきてしまってでかいので、下記のように、使用言語を限定している。 

```js
import hljs from 'highlight.js/lib/highlight'
import javascript from "highlight.js/lib/languages/javascript"
import css from "highlight.js/lib/languages/css"
import yaml from "highlight.js/lib/languages/yaml"
import python from "highlight.js/lib/languages/python"
import php from "highlight.js/lib/languages/php"
import shell from "highlight.js/lib/languages/shell"
import swift from "highlight.js/lib/languages/swift"

// mounted()とか任意の初期化タイミングで
hljs.registerLanguage("javascript", javascript)
hljs.registerLanguage("css", css)
hljs.registerLanguage("yaml", yaml)
hljs.registerLanguage("python", python)
hljs.registerLanguage("php", php)
hljs.registerLanguage("shell", shell)
hljs.registerLanguage("swift", swift)
```

### フォルダ構成

フォルダ構成は下記の通り。 

```bash
.
├── dist
│　　 ├── scripts
│　　 └── styles.css
├── footer.php
├── functions.php
├── header.php
├── index.php
├── package-lock.json
├── package.json
├── screenshot.jpg
├── src
│　　 ├── App.vue
│　　 ├── Constants.js
│　　 ├── api
│　　 │　　 ├── Repository.js
│　　 │　　 ├── RepositoryFactory.js
│　　 │　　 └── Repositoties
│　　 │　　     ├── CategoriesRepository.js
│　　 │　　     ├── ...
│　　 │　　     └── UsersRepository.js
│　　 ├── assets
│　　 │　　 └── scss
│　　 │　　     ├── ...
│　　 │　　     └── global.scss
│　　 ├── bootstrap.js
│　　 ├── components
│　　 │　　 ├── Category.vue
│　　 │　　 ├── Home.vue
│　　 │　　 ├── NotFound.vue
│　　 │　　 ├── Page.vue
│　　 │　　 ├── Post.vue
│　　 │　　 ├── Search.vue
│　　 │　　 ├── Tag.vue
│　　 │　　 ├── partials
│　　 │　　 └── widgets
│　　 ├── main.js
│　　 ├── router
│　　 │　　 └── index.js
│　　 └── store
│　　     ├── actions.js
│　　     ├── getters.js
│　　     ├── index.js
│　　     ├── modules
│　　     │　　 ├── category.js
│　　     │　　 ├── common.js
│　　     │　　 ├── menu.js
│　　     │　　 ├── page.js
│　　     │　　 ├── post.js
│　　     │　　 ├── site.js
│　　     │　　 ├── tag.js
│　　     │　　 └── user.js
│　　     └── mutation-types.js
├── style.css
└── webpack.config.js
```

|dir|desc|
|---|---|
|dir|ビルドしたjsとcss|
|*.php|wordpressのテンプレファイル|
|screenshot.jpg|サムネ用|
|src/api|API関連の実装|
|src/store|vuex store関連|
  
wordpressのテンプレートとして認識されるために、index.phpやstyle.css等、最低限必要なものを準備している。 エントリーポイントであるindex.phpと、vuejsのmain.jsは下記の通り。 

```html
<!-- index.php -->
<?php get_header(); ?>

<div id="app"></div>

<?php get_footer(); ?>
```

```js
// src/main.js
require('./bootstrap')

import Vue from 'vue/dist/vue.runtime.esm'
import router from './router'
import App from './App'
import store from './store'
import 'reset-css'

require('./assets/scss/global.scss')

Vue.config.productionTip = false

// html内のタグを除去してテキストにする
Vue.filter('striphtml', function (value) {
    const div = document.createElement("div");
    div.innerHTML = value;
    return div.textContent || div.innerText || "";
})

// 日付出力
Vue.filter('moment', function (date) {
    return dayjs(date).format('YYYY年MM月DD日');

})

const main = new Vue({
    router,
    store,
    render: h => h(App)
}).$mount('#app')
```

あとは通常のSPAと同じようにフロント部分を作り込めばOK。 

### API周り

#### RepositoryFactoryパターン

参考にさせてもらったリポジトリと同じようにapiディレクトリを切って、その中にパス毎にAPIアクセス処理を実装している。

ただ、axiosが乱立しそうな予感がプンプンしていたので、下記の記事を参考にして、RepositoryFactoryパターンを採用した。 原文：

[Vue API calls in a smart way &#8211; CanariasJS &#8211; Medium][2]   
日本語訳：[【Vue.js】Web API通信のデザインパターン (個人的ベストプラクティス) &#8211; Qiita][3] 

#### Repository

Repositoryは、「APIアクセス（コネクション確立、リクエスト作成、レスポンスのparse　等）を意識せずにデータを扱うためのクラス」

 JavaとかPHPとかで出てくるRepositoryも役割は基本的に同じで、接続する対象が単に「API」ではなく「DB」になったもの（というか個人的にはそっちの方がなじみ深い）。 

#### Factory

FactoryっていうのはここではFactory Methodのことと思われる。このパターンを採用すると、インスタンスを生成するのにnewを使用しない代わりに、Factory Methodの引数にインスタンスを作成したいクラスの識別子（任意に設定）を指定できる。

そうすることで、もしクラスの名称とかが変わってもインスタンス生成箇所の変更は不要になる（依存度が下がる）。

で、簡単に生成するクラス（Repository）を切り替えることができるので、テスト環境とかでモックを使って処理を行いたいときとかに便利。

結局vuexのstoreまわりでしかRepositoryを使用しなかったので、依存度を下げることのメリットはそこまで享受できなかったが、ソースの見通しは良くなったし、結果オーライな感じ。 

#### API系のプラグイン

今回関連記事、人気記事、メニューのAPI経由による取得処理にいくつかプラグインを使用した。 

  * Related Posts By Taxonomy
  * WP-REST-API V2 Menus
  * WordPress Popular Posts

### 最後に

とりあえずはしばらくこのテーマでブログを運営していこうと思う。

今後は、既存のテーマをSPA化したりして色々使い道を探っていきたい。

SEOも最近はSPAサイトにもやさしくなってきたらしい（そもそも今回のケースはSSRしているけども）ので、手軽にSPAテーマを作成できるようになればこれもまた武器になるんじゃないかなぁ。

 [1]: https://github.com/EvanAgee/vuejs-wordpress-theme-starter
 [2]: https://medium.com/canariasjs/vue-api-calls-in-a-smart-way-8d521812c322
 [3]: https://qiita.com/07JP27/items/0923cbe3b6435c19d761
