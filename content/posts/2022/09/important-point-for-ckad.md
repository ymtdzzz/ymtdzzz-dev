---
title: " 【2022年6月〜】新環境でCKADを受験する際の注意点について"
date: 2022-09-07
tags:
  - "CKAD"
  - "Kubernetes"
published: true
category: Diary
---

## TL;DR

- Verify Name（本人確認用名前）がアルファベットの場合に運転免許証＋クレジットカードの組み合わせで本人確認できなくなった
    - パスポートが無い場合はおとなしくVerify Nameも漢字を入れるべき
- PSI secure browserの起動ボタンが反応しなかったら開発者ツールを開いてクリックすると上手くいく
- トラブルで受験できなかった場合はサポートチケットを切ろう
    - 例外的に試験回数を受験前に戻してくれる可能性がある

## CKAD取得

先週受験したCKAD、無事合格できたのですが、ちょっと以前CKAを受けたときと色々受験方法が変わっていて困惑したので、受験当時の流れを振り返ってみたいと思います。

トラブルもありましたが、基本的に自分の確認ミスだったのと、サポートが懇切丁寧に対応してくださったおかげで最終的には受験できたわけですが、以前Linux Foundation主催の試験を受けた人は混乱しそうな部分もありそうなので記事にしました。

## 受験の記録

### 申込みと受験日設定

申込み自体はこれまで通りできました。

[https://training.linuxfoundation.org/ja/certification/certified-kubernetes-application-developer-ckad-jp/](https://training.linuxfoundation.org/ja/certification/certified-kubernetes-application-developer-ckad-jp/)

今回受験したのはCKAD-JPです。日本語版はちょっと高いのですが、会社がお金出してくれるので遠慮なく。

支払いまで完了すると受験日の設定の案内が来て、数日後〜で好きな日時で設定したら完了です。

### 事前準備

試験当日までにいくつかやらないといけないことがあります。

- ドキュメントの確認（規約、受験上の注意など）
    - リンクを開くだけでOKですが、**ちゃんと読みましょう（自戒）**
- 受験環境のチェック
    - 画面とか音声の共有とか、ネットワークのスループットなど
- Verify Name（本人確認用名前）の入力
    - 以前CKAを受験したときと同様アルファベットで入力しました
    - **【注意】パスポート持ってないのでここは漢字じゃないとだめでした。**

### 試験当日、受験できず

部屋の掃除をして、いざ受験。

しかし、本人確認の段階でProctorから「名前が一致しないので受験できません」と言われ、残念ながら受験できませんでした。

半年前くらいにCKAを受験した際は「運転免許証」と「クレジットカード」でOKだったのですが、いつの間にかその組み合わせが使えなくなっていたみたいです。

### サポートに問い合わせ

サポートチケットを起票して下記の点を問い合わせました。

※基本的に全部英語でのやりとりになります

- 運転免許証とクレジットカードによる本人確認はできなくなったのか
- Verify Nameに日本語を使用するのは問題無いか

問い合わせは下記から（Jiraですね）。

[https://training.linuxfoundation.org/ja/about/contact-us/](https://training.linuxfoundation.org/ja/about/contact-us/)

### サポートからの回答

Q. 運転免許証とクレジットカードによる本人確認はできなくなったのか

A. ドキュメントに記載ある通り、Verify Nameとprimary ID（ここでいう運転免許証）の名前は完全に一致しなければならない。なので、Verify Nameをアルファベットで書いちゃったなら当然受験できない。

ドキュメント：[https://docs.linuxfoundation.org/tc-docs/certification/tips-cka-and-ckad#id-requirements-to-take-the-exam](https://docs.linuxfoundation.org/tc-docs/certification/tips-cka-and-ckad#id-requirements-to-take-the-exam)

> The first and last name on the ID **must exactly match** [the verified name](https://docs.linuxfoundation.org/tc-docs/certification/lf-handbook2/exam-preparation-checklist#verify-name) entered on your exam checklist
> 

**すいません、ちゃんと書いてありました。**

ということで、Verify Nameを日本語で書けばいいということになりますが、そもそも日本語自体対応してなかったらどうしようとということで投げた２つ目の質問についても回答が来てました。

Q. Verify Nameに日本語を使用するのは問題無いか

A. 使えます。何度も言うけどVerify Nameと全く同じ名前になっていることを確認してね。あと、今回は**一回限りの例外として、受験回数リセットしておいた**から。

### 再試験

非常に寛大な措置にお礼の返信をしつつ、再度受験日の調整から行い、今度こそVerify Nameを日本語で記載し無事受験することができましたとさ。

ただ、受験する際にpsi secure browserという専用ブラウザを使用する必要があるのですが、**起動するボタンが反応せず**、最終的になぜか開発者ツールを開くことで起動できました。ﾅﾝﾃﾞ?

### 試験結果

Scoreは96で、かなり余裕を持って合格できました（合格点66）。受験難易度自体はCKAよりも低かったかも。

Udemyの下記講座を一通り流せば合格できると思います。
[https://www.udemy.com/course/certified-kubernetes-application-developer/](https://www.udemy.com/course/certified-kubernetes-application-developer/)

## まとめ

親切なサポート対応のおかげでだいぶ救われました。パスポート持ってない人はVerify Nameは絶対日本語で登録するようにしましょう。

もしトラブルが起きたら落ち着いてサポートチケットを起票して問い合わせましょう。google翻訳で十分です。

また、当然ですが、受験上の注意はちゃんと読みましょう。正直以前CKAを受けていたので油断してました。すいません。

[https://docs.linuxfoundation.org/tc-docs/certification/tips-cka-and-ckad](https://docs.linuxfoundation.org/tc-docs/certification/tips-cka-and-ckad)
