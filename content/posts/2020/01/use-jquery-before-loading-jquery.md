---
title: "jQuery読み込み前にjQueryを書きたい"
date: 2020-01-19
tags:
  - "javascript"
  - "jQuery"
published: True
category: Programming
---
## 事象

テンプレートエンジンを使用したWebアプリケーションの構築を複数人でやっていると、大体骨組みはリードエンジニアが作成して、そこにincludeするviewを各エンジニアが作成するという流れを採用すると思う。

各開発者が作成するviewも雛形があって、「ここにjavascriptを書いてね」とか「ここにスタイルを書いてね」とか、そういう指定がある。 

<!--more-->

Twigなら、ベースレイアウトが以下のようになっていて 

```twig
{# layout.twig #}
<head>
{# ヘッダとか色々 #}
{% if block("style") is defined %}{{ block('style') }}{% endif %}
</head>
{{ block('content') }}
<script src="./path/to/jquery.js"></script>
{{ block('script') }}
```

各開発者は、以下のようにviewを作成する。 

```twig
{# form.twig #}
{% extends 'layout' %}

{% block content %}
<form>
...
</form>
{% endblock %}

{% block style %}
form.text_form {
    color: red;
    //...
}
{% endblock %}

{% block style %}
<script>
    function func() {
        $forms = $('.form');
        //...
    }
</script>
{% endblock %}
```

このルールに則った（＝layout.twigを継承した）viewを作成するには差し支えないが、例えば、色々なところでincludeできるパーツ（モーダルウィンドウとか）を作成したい場合、不都合が生じる。

最近は、レンダリングブロックを回避するために、jsのライブラリは最後に読み込むプロジェクトが多いと思う。 

layout.twigを継承した場合、きちんとjsを書くためのblockが定義されており、そこに記述すればjquery読み込み後に挿入してくれるため、特に問題無くjqueryを使用することが可能である。 

しかし、layout.twigを継承するパーツをさらに継承したパーツを作る場合

> layout.twig←各開発者が作成したview←作成する共通パーツ 

という順になるため、共通パーツはすべてlayout.twigでいうところのcontent blockにしか入れることができない。 

すると、jqueryの文法（$(&#8216;hogehoge&#8217;)とか）を使用した時点でエラーが吐かれる。 

## 解決方法

「どうすればいいですか」とリードエンジニアに聞いたら一瞬で回答が返ってきた。 

作成した共通パーツのJS記述を下記のようにする。

```html
<script>
(function () {
    var func = function () {
        // ここに実行したい処理
    }
    if (typeof($) === 'undefined') {
        window.addEventListener('load', func, false);
    } else {
        func();
    }
})();
```

やってることは単純で、jquery読み込み後に実行してほしいコードをfunc変数に関数として格納しといて、ページ読み込み完了後（=jquery読み込み完了後）に実行するようにイベントリスナーを設定しておく。 

あとはloadイベントが発火したらそのスクリプトが実行されるね　という感じ。
