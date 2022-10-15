---
title: "FlutterにおけるBLoCパターンについて"
date: 2020-02-24
tags:
  - "Android"
  - "BLoC"
  - "Dart"
  - "Flutter"
  - "iOS"
published: True
category: Programming
---
## はじめに

モバイルアプリで作りたいものがあり、只今技術選定中。せっかくなのでモダンなフレームワークを使いたいと考えていたところ、Flutterが今盛り上がっているっぽいので色々チュートリアルを読みながら勉強した。 

今回は、色々チュートリアル巡りをしていて、業務レベルのアプリを作るときにも使えそうなBLoCパターンをまとめる。 

<!--more-->

## BLoCパターン概要

「Business Logic Component」の略。状態のインプット、アウトプットをdartのStreamに限定して行うことで、データの一方通行化を実現する。

![](../../../../gridsome-theme/src/assets/images/old/wordpress/ef72fa8c5e5212ed403a051987637e90-800x480.png)

### 登場人物

  * API Provider 実際に外部サーバとAPI通信を行う人。この図だと、受け取ったJSONデータをデコードしてインスタンスオブジェクトに変換する責務も負っているが、Repositoryが行う場合もある。 

  * Repository データの取得を行う。通常のRepositoryパターンと同様、通信相手がAPIなのかデータベースなのかといったことは意識せずにデータのやりとりを行うことを可能にする。 

  * Model JSONデータとインスタンスオブジェクトとのマッピングを定義するクラス。

[このサイト][1]を使うと、モデルの構成を渡すだけでモデルクラスを作成してくれるのでとても便利。 

  * BLoC 状態管理クラス。Repositoryからデータを取得し、データ加工後Streamに流して状態を更新する。Widgetにおいては、BLoCから流れたデータをキャッチして該当箇所が再描画される。Screen(Widgetの集まり)毎にBLoCが存在するイメージ。 

### フォルダ構成(案)

チュートリアル

[Architect your Flutter project using BLOC pattern][2]では、下記のようなフォルダ構成をしていた。 

```bash
lib
 ┣ src
 ┃ ┣ blocs
 ┃ ┃ ┗ hoge_bloc.dart
 ┃ ┣ models
 ┃ ┃ ┗ hoge_model.dart
 ┃ ┣ resources
 ┃ ┃ ┣ hoge_api_provider.dart
 ┃ ┃ ┗ repository.dart
 ┃ ┣ ui
 ┃ ┃ ┗ hoge_list.dart
 ┃ ┗ app.dart
 ┣ main.dart
 ...
 ```
 
 このあたりについては色々な組み方がありそうだが、bloc/resources/uiが分かれていれば何でも良さそう。 

## 各コンポーネント

### API Provider 実際にAPIやDBと通信するコンポーネント。 

```dart
import 'dart:async';
import 'package:http/http.dart'  show Client;
import 'dart:convert';
import '../models/hoge_model.dart';

class HogeApiProvider {
  Client client = Client();
  final _baseUrl = "http://api.example.com";

  Future&lt;HogeModel> fetchHogeList() async {
    final response = await client
      .get("$_baseUrl/list");
    print(response.body.toString());
    if (response.statusCode == 200) {
      return HogeModel.fromJson(json.decode(response.body));
    } else {
      throw Exception('Failed to fetch hoge list!');
    }
  }

  // ...
}
```

### Repository

API Providerを使用してデータの取得を行うコンポーネント（APIとの通信を隠蔽）。 

```dart
import 'dart:async';
import 'movie_api_provider.dart';
import '../models/hoge_model.dart';

class Repository {
  final hogeApiProvider = HogeApiProvider();

  Future&lt;HogeModel> fetchAllHoge() =>
      hogeApiProvider.fetchHogeList();
}
```

### Model

JSONデータをオブジェクトにマッピングするクラス。 

```dart
Hoge hogeFromJson(String str) => Hoge.fromJson(json.decode(str));
String hogeToJson(Hoge data) => json.encode(data.toJson());

class Hoge {
    int hogeId;
    String hogeName;

    Hoge({
        this.hogeId,
        this.hogeName,
    });

    factory Hoge.fromJson(Map&lt;String, dynamic> json) => Hoge(
        hogeId: json["hoge_id"],
        hogeName: json["hoge_name"],
    );

    Map&lt;String, dynamic> toJson() => {
        "hoge_id": hogeId,
        "hoge_name": hogeName,
    };
}
```

### BLoC

状態管理クラス。ここからstreamにデータをaddする（流す）ことで、Widget側のStreamBuilderが再描画される。 

```dart
// hoge_bloc.dart
class HogeBloc {
  final _repository = Repository();
  final _hogeFetcher = PublishSubject&lt;Hoge>();

  Observable&lt;Item> get allHoge => _hogeFetcher.stream;

  fetchAllHoge() async {
    Hoge hoge = await _repository.fetchAllHoge();
    _hogeFetcher.sink.add(hoge);
  }

  dispose() {
    _mhogeFetcher.close();
  }
}
```

また、blocを供給するProviderクラスも作成する。 

```dart
// hoge_bloc_provider.dart
class HogeBlocProvider extends InheritedWidget {
  final HogeBloc bloc;

  HogeBlocProvider({Key key, Widget child})
    : bloc = HogeBloc(),
      super(key: key, child: child);

  @override
  bool updateShouldNotify(_) {
    return true;
  }

  static HogeBloc of(BuildContext context) {
    return (context.inheritFromWidgetOfExactType(HogeBlocProvider)
    as HogeBlocProvider).bloc;
  }
}
```

実際に上記のBLoCを利用するViewでは、上記のProviderを親要素として、子要素にそのblocを利用したいViewを読み込ませる。 

```dart
return HogeBlocProvider(
      child: HogeHogeView(
          //...
      ),
    );
```

## 終わりに

公式ドキュメントだと、簡単な状態管理についてはChangeNotifierとProviderを使用して行う方法を[推奨しているっぽい][3]ので、BLoCの採用については今作ろうとしているアプリの要件を考慮しつつ慎重に考える必要がありそう。

 [1]: https://app.quicktype.io/#l=dart
 [2]: https://medium.com/flutterpub/architect-your-flutter-project-using-bloc-pattern-part-2-d8dd1eca9ba5
 [3]: https://flutter.dev/docs/development/data-and-backend/state-mgmt/simple#changenotifier
