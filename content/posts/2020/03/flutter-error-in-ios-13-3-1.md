---
title: "Flutterが最新iOS(13.3.1)のiPhone実機でコケる問題"
date: 2020-03-08
tags:
  - "Flutter"
  - "iOS"
  - "iOS13.3.1"
  - "XCode"
published: True
category: Programming
---
## 経緯

ビルドして実機で確認しようとすると、スプラッシュ画面で下記のようなエラーが発生してコケる問題に遭遇した。 

<!--more-->

```bash
dyld: Library not loaded: @rpath/Flutter.framework/Flutter
  Referenced from: /private/var/containers/Bundle/Application/CE491C25-9C7E-4FF6-A3FE-10D8904366B1/Runner.app/Runner
  Reason: no suitable image found.  Did find:
    /private/var/containers/Bundle/Application/CE491C25-9C7E-4FF6-A3FE-10D8904366B1/Runner.app/Frameworks/Flutter.framework/Flutter: code signature invalid for '/private/var/containers/Bundle/Application/CE491C25-9C7E-4FF6-A3FE-10D8904366B1/Runner.app/Frameworks/Flutter.framework/Flutter'
```

## 環境

  * macOS Catalina 10.15.3
  * iPhone 7 iOS13.3.1

```bash
$ flutter doctor
[✓] Flutter (Channel stable, v1.12.13+hotfix.8, on Mac OS X 10.15.3 19D76,
    locale ja-JP)

[✓] Android toolchain - develop for Android devices (Android SDK version 29.0.2)
[✓] Xcode - develop for iOS and macOS (Xcode 11.3.1)
[✓] Android Studio (version 3.5)
[✓] VS Code (version 1.42.1)
```

## とりあえず色々やってみたこと

  * Flutterのバージョンを上げる
  * ビルド設定（Runner.xcodeproj）側の設定見直し
      * Apple Developerの証明書をキーチェーから削除して再作成
      * Provisioning Certificateの再作成
  * Flutter configでProvisioning Profileを直接指定

```bash
$ vi ~/.flutter_settings
{
  "ios-signing-cert": "Apple Development: hoge@huga.com (XXXXXXXXXX)"
}
```

証明書とかProvisioning Profileの問題でも無いっぽい？ 

`flutter run -v`を試す。 

```bash
[        ] (lldb)     connect
[  +28 ms] (lldb)     run
[ +153 ms] success
[        ] (lldb)     safequit
[ +110 ms] Process 392 detached
[  +41 ms] Application launched on the device. Waiting for observatory port.
[   +3 ms] Checking for advertised Dart observatories...
[+5019 ms] mDNS lookup failed, attempting fallback to reading device log.
[        ] Waiting for observatory port.
```

このエラーでissueを調べたらこんなコメントがあった。 

> @gitgeekaus Are you on Catalina? Go to System Preferences > Network > iPhone USB > uncheck &#8220;Disable unless needed&#8221; > Apply. This was the problem for me.

[iOS mDNS meta issue #46705][1] 

自分の環境の場合、ネットワーク設定の「iPhone USB」という項目自体が存在しなかったが、iPhoneのインターネット共有を有効にしたら出てきた。 

「不要なら無効化する」的な項目をオフにしたが、やはりエラーは変わらず。 

## 解決法

さらに色々調べた結果、こんなissueコメントを発見。 

> Install the beta profile on your test device and install iOS 13.4 beta 3. Wait for iOS 13.4 to be released. Use a non-Personal Team provisioning profile. Personal Team provisioning profile says &#8220;Personal Team&#8221; in the Xcode build settings Runner Target > General > Signing and Capabilities > Team dropdown. Run in the simulator. Test on a iOS device running 13.3 or lower.

[Running new app on actual iOS (13.3.1) device crashes on startup: code signature invalid for &#8220;path/to/Flutter.framework/Flutter&#8221; #49504][2] 

要するに、 

  * 実機のiOSが13.3.1だと再現するため、13.4(beta3)使用する
  * 正式版13.4がリリースされるのを待つ
  * personalじゃないprovisioning profileを使用する
  * シミュレータで動作確認する
  * 13.3以下のiOSの実機を使用する てことらしい・・・。 

まだ絶賛開発中のアプリなので、一旦シミュレーションで我慢する。 

・・・と、ここまで書いたら同じ内容の記事を発見してしまった。 

[Flutterの実機デバッグでInstalling and launching…から変わらない問題][3]

 [1]: https://github.com/flutter/flutter/issues/46705#issuecomment-566813481
 [2]: https://github.com/flutter/flutter/issues/49504#issuecomment-592767041
 [3]: https://ttydev.com/2020/02/14/post-514/
