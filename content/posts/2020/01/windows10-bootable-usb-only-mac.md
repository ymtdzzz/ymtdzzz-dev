---
title: "MacだけでWindows10のインストールメディア（USB）を作成する"
date: 2020-01-19
tags:
  - "Mac"
  - "unetbootin"
  - "USB"
  - "Windows10"
published: True
category: Diary
---
## 経緯

いや、もちろんWindowsで作成するのが一番手っ取り早いんだけども、どうしてもMacを使わなざるを得ない状況に陥ってしまったので。

<!--more-->

### Windowsマシンのマザボ交換

デスクトップマシンが流石に古くなってきたので、パーツ交換＆Windows10へのアップグレードを計画した。 

新調したパーツは以下の通り 

|Part|Name|
|---|---|
|Motherboard|ASUS PRIME Z390-A|
|CPU|9th gen Intel Corei5 9400|
|MEM|16GB（メーカー忘れた）|
  
お金もないのでスペック控え目。これで大体５万円程度。 

マザボ交換なんて普段しないのでわりとグダりつつBIOS起動まで持っていった。 

### Windows7インストール不可

もちろんWindows10をインストールするつもりでいたが、手元にあるのはWindows7のインストールディスクだったので、 

>  * 一旦インストールディスクからWindows7をインストール＆起動
>  * Windows7からWindows10にアップグレード
  
こんな感じのフローを思い描いていた。 

Windwos10のインストールメディアを作成するための外部デバイスが見つからなかったし、まあなんとかなるだろうと思っていた。 

ただ、購入したCPUは第9世代Coffee Lake Refreshプロセッサ。

**Windows7はもちろん動作対象外。** やってもーた。 

### どうしよう&#8230;

どうしようと思って色々考えた方法。 

  * なんとかしてマウスとキーボードを認識させる
    →無理。
    
  * MacでPXEサーバを立ててネットワーク経由でインストール
    →情報古い＆少ない＆時間がない
    
  * 旧マザボを接続し直してインストールメディアを作成する
    →また組み直すのがめんどくさかったので最終手段
    
  * Macでインストールメディアを作成する
  
ということで、Macでインストールメディアを作成することになった。幸いUSBは32GBのものを発見。 

## 環境

手元の環境は下記の通り。 

```
MacBook Pro (13-inch, 2018, Four Thunderbolt 3 Ports)
MacOS Catalina 10.15.1 
```

※USB type-Cとtype-Aの変換アダプタは近所のダイソーで購入。 

## 作成方法

結論だけ知りたい方は方法④だけ見ておけばOKだが、色々苦労したので経緯を踏まえて書き残しておく。 

### 方法①

unetbootinを使用 unetbootinを使用すれば、Macでもwindows10用のブートメディアを作成できると聞いて、

[公式ページ][1]からダウンロードしてインストール。 

AppStoreからダウンロードしたものではないので、起動するための設定を一通りしてから起動するも、Windowが開かず。 

再起動したり再インストールしても同じ現象に見舞われたので一旦別の手段を探すことに。 

### 方法②

他のBootable USB作成ソフトを使用 他にMacでブートメディアを作成できるツールがないか探した。 

  * Etcher：ISOをUSBに書き込むことができたが、「Windowsのインストールメディアは非推奨だから違うアプリを使った方がいいよ」っていう警告が出る。 

無視して続行して作成したUSBでブートしてみるも、インストールメディア選択画面でUSBが認識されず。 

  * Deepin Boot Maker：Etcherと同様、上手くいかなかった。 

### 方法③ ddコマンドで作成

[MacでWindows10のISOイメージをUSBメモリへ書き込む][2] 上記の記事を参考に、Terminalからコマンドで焼く方法を試した。 

しかし、結局方法②と同じで、ブートはできるもののインストール時にUSBとして認識されていない様子。 

### 方法④ unetbootinをなんとかして起動させる

やっぱりunetbootinを使わないとだめか・・・ということで、何とかして起動する方法を探す。 

メニューバーは表示されていて、起動自体はできているっぽい。ということは最新OSに対応していないだけか・・・？と睨む。 

最新OS対応に関わる問題であれば、Githubにissueが立ってるかも　と思い、調べた結果。 [Wont run in macOS Catalina (macOS 10.15) #223][3] あった。 

```bash
sudo /Applications/unetbootin.app/Contents/MacOS/unetbootin method=diskimage isofile="/Users/usernamehere/Downloads/Boot USB/WinPE10_8_x86_x64_2019.10.02_English.iso" installtype=USB targetdrive=/dev/disk6
```

これを実行したら普通にGUIが表示された。
（パラメータはでたらめなので、GUI上で正しいISOファイルとドライブを指定。） 

これでブートメディアを作成したら、上手くインストールすることができた。 

注意点として、

**USBをフォーマットするときは必ず「exFAT」を指定すること。** FAT32でやると、起動イメージ自体の容量が4GBを超過して上手くインストールするいことができないので。 

## Windows10快適

色々あったけど、なんとかWindows10を入れることができた。 

デスクトップマシンは長らくHDD＋Windows7を使っていたので、SSD+Windows10で超爆速になって満足。 

相変わらずグラボはGTX680という化石を使っているので、そのうちグラボも買い替えたい・・・。

 [1]: https://unetbootin.github.io/
 [2]: https://www.laddy.info/2019/01/29247/
 [3]: https://github.com/unetbootin/unetbootin/issues/223#issuecomment-559970620
