---
title: "【Swift5.0】ESTabBarControllerでタブをカスタマイズする"
date: 2019-09-03
tags: 
  - "Swift"
  - "ESTabBarController"
  - "iOS"
published: True
category: Programming
---

## **タブをカスタマイズしたい**

最近はSwiftでアプリを作っています（プライベートで）。 

タブをちょいおしゃれな感じにしたいなーと思って色々ライブラリを漁っていたところ、「[ESTabBarController][1]」っていうライブラリがなんだか良さげだったのでテストがてら触ってみました。 

<!--more-->

有名なライブラリみたいなんですが、tutorial的なものが無かったので作者さんのexampleプロジェクトを見ながら実装しました。

ただ、Swift経験が浅いのもあってちょこっと手こずったので、今回はチュートリアル形式で記事にしておきたいと思います。 最終的には以下のような動作を実現します。

![](../../../../gridsome-theme/src/assets/images/old/wordpress/center_big_tab.gif)

## **ライブラリの導入**

ちなみにこのプラグインはCocoapodsとCarthage両方対応しています。 

今回はビルド時間を考慮して、Carthageで入れられるものは基本的にCocoapodsは使わずにCarthageで導入しています。 プロジェクト作成後、プロジェクト直下に移動してCartfileを作成します。 

```bash
$ cd your/project/folder/path
$ touch Cartfile
```

今回はESTabBarControllerと、popライブラリを導入しますので、下記の通りCartfileを編集します。 

```bash
github "eggswift/ESTabBarController"
github "facebook/pop"
```

Carthageコマンドで導入を行います。 

```bash
$ carthage update --platform iOS
```

上記コマンドを実行すると、下記の通りファイル/ディレクトリが作成されます。 

  > Carthage.resolved- Carthage/Build- Carthage/Checkouts
  
プロジェクトファイル（xcodeproj）を開いて、[General]タブ内、[Linked Frameworks and Libraries]の[+]を押下して、[Add other]を選択します。その後、下記2ファイルを追加します。 

  > (ProjectRoot)/Carthage/Build/iOS/ESTabBarController.framework
  > (ProjectRoot)/Carthage/Build/iOS/pop.framework

[Build Phases]タブ、左上の[+]で[New Run Script Phrase]を押下して、追加された[Run Srcipt]内、shellコマンドの入力エリアで下記コマンドを追記。 

bash/usr/local/bin/carthage copy-frameworks 同エリア内、[Input Files]の[+]で下記のパスを追加。 

```bash
$(SRCROOT)/Carthage/Build/iOS/ESTabBarController.framework
$(SRCROOT)/Carthage/Build/iOS/pop.framework
```

あとはソースファイル内でimportすれば自由に利用できます。 

## **とりあえず普通のタブバーを作る**

ひとまず普通のタブバーを作りたいと思います。

![](../../../../gridsome-theme/src/assets/images/old/wordpress/normal_tab.gif)

### **storyboardの作成**

今回作成するアプリの画面構成は下記の通りです。タブごとにstoryboardを分けています。 

  * Main.storyboard : アプリのエントリポイント＋タブの制御
  * First.storyboard : １つ目（左）のタブ選択時に表示（今回は使用しない）
  * Second.storyboard : 2つ目（真ん中）のタブ選択時に表示
  * Third.storyboard : 3つ目（右）のタブ選択時に表示（今回は使用しない）

### **コントローラーの作成**

はじめに「MainTabViewController.swift」を作成し、Main.storyboardのinitialViewControllerにアタッチします（デフォルトの「ViewController.swift」はいらないので削除）。

![](../../../../gridsome-theme/src/assets/images/old/wordpress/01_attach_to_mainStoryboard.png)

MainTabViewControllerにコードを追加する前に、ESTabBarを制御する「TabBarContentViewController.swift」を作成します。 まずは通常タブ（tabBarItem）用のクラスを下記の通り定義します（作成時に自動付与されるクラス名から変更していることに注意）。 

```swift
    // MainTabViewController.swift
    import UIKit
    import ESTabBarController
    import pop
    
    class TabBarBasicContentView: ESTabBarItemContentView {
        public var duration = 0.3
        
        override init(frame: CGRect) {
            super.init(frame: frame)
            textColor = UIColor.init(white: 50.0 / 255.0, alpha: 1.0)
            highlightTextColor = UIColor.init(red: 254/255.0, green: 73/255.0, blue: 42/255.0, alpha: 1.0)
            iconColor = UIColor.init(white: 50.0 / 255.0, alpha: 1.0)
            highlightIconColor = UIColor.init(red: 254/255.0, green: 73/255.0, blue: 42/255.0, alpha: 1.0)
        }
        
        public required init?(coder aDecoder: NSCoder) {
            fatalError("init(coder:) has not been implemented")
        }
        
        override func selectAnimation(animated: Bool, completion: (() -> ())?) {
            self.bounceAnimation()
            completion?()
        }
        
        func bounceAnimation() {
            let impliesAnimation = CAKeyframeAnimation(keyPath: "transform.scale")
            impliesAnimation.values = [1.0 ,1.4, 0.9, 1.15, 0.95, 1.02, 1.0]
            impliesAnimation.duration = duration * 2
            impliesAnimation.calculationMode = CAAnimationCalculationMode.cubic
            imageView.layer.add(impliesAnimation, forKey: nil)
        }
    
    }
```
    
selectAnimation()をオーバーライドすることで好きなアニメーションを実行することができます。 続いて、ナビゲーションバーのコントローラー「MainNavigationController.swit」も作成し、下記の通り記述します。 

```swift
// MainNavigationController.swit
import UIKit

class MainNavigationController: UINavigationController {

    override func viewDidLoad() {
        super.viewDidLoad()
        let appearance = UIBarButtonItem.appearance()
        appearance.setBackButtonTitlePositionAdjustment(UIOffset.init(horizontal: 0.0, vertical: -60), for: .default)
        self.navigationBar.isTranslucent = true
        self.navigationBar.barTintColor = UIColor.init(red: 250/255.0, green: 250/255.0, blue: 250/255.0, alpha: 0.8)
        #if swift(&gt;=4.0)
        self.navigationBar.titleTextAttributes = [NSAttributedString.Key.foregroundColor : UIColor.init(red: 38/255.0, green: 38/255.0, blue: 38/255.0, alpha: 1.0), NSAttributedString.Key.font: UIFont.systemFont(ofSize: 16.0)]
        #elseif swift(&gt;=3.0)
        self.navigationBar.titleTextAttributes = [NSForegroundColorAttributeName : UIColor.init(red: 38/255.0, green: 38/255.0, blue: 38/255.0, alpha: 1.0), NSFontAttributeName: UIFont.systemFont(ofSize: 16.0)];
        #endif
        self.navigationBar.tintColor = UIColor.init(red: 38/255.0, green: 38/255.0, blue: 38/255.0, alpha: 1.0)
        self.navigationItem.title = "Example"
    }
}
```

tabBarItemのコントローラとナビゲーションバーのコントローラーができたので、「MainTabViewController.swift」を下記の通り編集します（画像はESTabBarControllerのリポジトリのexampleから持ってきてます）。 

```swift
// MainTabViewController.swift
import UIKit
import ESTabBarController

class MainTabBarController: ESTabBarController {
    override func viewDidLoad() {
        super.viewDidLoad()
    }
    
    required init?(coder aDecoder: NSCoder) {
        super.init(coder: aDecoder)
        
        let v1 = UIStoryboard(name: "First", bundle: nil).instantiateInitialViewController()
        v1?.tabBarItem = ESTabBarItem.init(TabBarBasicContentView(), title: "Home", image: UIImage(named: "home"), selectedImage: UIImage(named: "home_1"), tag: 1)
        v1?.title = "Home"
        
        let v2 = UIStoryboard(name: "Second", bundle: nil).instantiateInitialViewController()
        v2?.tabBarItem = ESTabBarItem.init(TabBarBasicContentView(), title: "Find", image: UIImage(named: "find"), selectedImage: UIImage(named: "find_1"), tag: 2)
        v2?.title = "Find"
        
        let v3 = UIStoryboard(name: "Third", bundle: nil).instantiateInitialViewController()
        v3?.tabBarItem = ESTabBarItem.init(TabBarBasicContentView(), title: "Me", image: UIImage(named: "me"), selectedImage: UIImage(named: "me_1"), tag: 3)
        v3?.title = "Me"
        
        let n1 = MainNavigationController.init(rootViewController: v1!)
        let n2 = MainNavigationController.init(rootViewController: v2!)
        let n3 = MainNavigationController.init(rootViewController: v3!)
        
        self.viewControllers = [n1, n2, n3]
    }
}
```

ここでは、tabBarItemやタイトルを含むUIViewController（①）とUINavigationController（②）を作成し、①を②のrootViewControllerとして設定しています。それらを3セット作成することでタブ3つ分準備しました。 

続いて、First.storyboardとSecond.storyboardとThird.storyboardについて、UIViewController（例:FirstViewController等）を作成＋initialViewControllerの設定を済ませ、Identity inspectorの[identity]内、[Storyboard ID]をそれぞれFirst,Second,Thirdとしておきます。

![](../../../../gridsome-theme/src/assets/images/old/wordpress/02_storyboard_settings.png)

これで、オーソドックスなナビゲーションバー＋アニメーション付きのタブバーは完成です。 

## **真ん中だけ大きいタブの作成**

続いて、最近よく見かける真ん中だけ大きくなっているスタイルのタブを作成します。今回はそれをタップするとカメラを起動orアルバムから追加するか選択するアクションが出てきます。

![](../../../../gridsome-theme/src/assets/images/old/wordpress/center_big_tab.gif)

### **コントローラーの編集**

まずは、真ん中のtabBarItemに適用するTabBarCenterContentViewクラスを「TabBarContentView.swift」に追加します。 

```swift
// TabBarContentView.swift
class TabBarCenterContentView: ESTabBarItemContentView {
    override init(frame: CGRect) {
        super.init(frame: frame)
        
        self.imageView.backgroundColor = UIColor.init(red: 23/255.0, green: 149/255.0, blue: 158/255.0, alpha: 1.0)
        self.imageView.layer.borderWidth = 3.0
        self.imageView.layer.borderColor = UIColor.init(white: 235 / 255.0, alpha: 1.0).cgColor
        self.imageView.layer.cornerRadius = 35
        self.insets = UIEdgeInsets.init(top: -32, left: 0, bottom: 0, right: 0)
        let transform = CGAffineTransform.identity
        self.imageView.transform = transform
        // これは何をする？
        self.superview?.bringSubviewToFront(self)
        
        textColor = UIColor.init(white: 255.0 / 255.0, alpha: 1.0)
        highlightTextColor = UIColor.init(white: 255.0 / 255.0, alpha: 1.0)
        iconColor = UIColor.init(white: 255.0 / 255.0, alpha: 1.0)
        highlightIconColor = UIColor.init(white: 255.0 / 255.0, alpha: 1.0)
        backdropColor = .clear
        highlightBackdropColor = .clear
    }
    
    public required init?(coder aDecoder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
    
    // タップ領域の指定
    override func point(inside point: CGPoint, with event: UIEvent?) -&gt; Bool {
        let p = CGPoint.init(x: point.x - imageView.frame.origin.x, y: point.y - imageView.frame.origin.y)
        return sqrt(pow(imageView.bounds.size.width / 2.0 - p.x, 2) + pow(imageView.bounds.size.height / 2.0 - p.y, 2)) &lt; imageView.bounds.size.width / 2.0
    }
    
    override func updateLayout() {
        super.updateLayout()
        self.imageView.sizeToFit()
        self.imageView.center = CGPoint.init(x: self.bounds.size.width / 2.0, y: self.bounds.size.height / 2.0)
    }
    
    override func selectAnimation(animated: Bool, completion: (() -&gt; ())?) {
        let view = UIView.init(frame: CGRect.init(origin: CGPoint.zero, size: CGSize(width: 2.0, height: 2.0)))
        view.layer.cornerRadius = 1.0
        view.layer.opacity = 0.5
        view.backgroundColor = UIColor.init(red: 10/255.0, green: 66/255.0, blue: 91/255.0, alpha: 1.0)
        self.addSubview(view)
        playMaskAnimation(animateView: view, target: self.imageView, completion: {
            [weak view] in
            view?.removeFromSuperview()
            completion?()
        })
    }
    
    public override func highlightAnimation(animated: Bool, completion: (() -&gt; ())?) {
        UIView.beginAnimations("small", context: nil)
        UIView.setAnimationDuration(0.2)
        let transform = self.imageView.transform.scaledBy(x: 0.8, y: 0.8)
        self.imageView.transform = transform
        UIView.commitAnimations()
        completion?()
    }
    
    public override func dehighlightAnimation(animated: Bool, completion: (() -&gt; ())?) {
        UIView.beginAnimations("big", context: nil)
        UIView.setAnimationDuration(0.2)
        let transform = CGAffineTransform.identity
        self.imageView.transform = transform
        UIView.commitAnimations()
        completion?()
    }
    
    private func playMaskAnimation(animateView view: UIView, target: UIView, completion: (() -&gt; ())?) {
        view.center = CGPoint.init(x: target.frame.origin.x + target.frame.size.width / 2.0, y: target.frame.origin.y + target.frame.size.height / 2.0)
        
        let scale = POPBasicAnimation.init(propertyNamed: kPOPLayerScaleXY)
        scale?.fromValue = NSValue.init(cgSize: CGSize.init(width: 1.0, height: 1.0))
        scale?.toValue = NSValue.init(cgSize: CGSize.init(width: 36.0, height: 36.0))
        scale?.beginTime = CACurrentMediaTime()
        scale?.duration = 0.3
        scale?.timingFunction = CAMediaTimingFunction.init(name: CAMediaTimingFunctionName.easeOut)
        scale?.removedOnCompletion = true
        
        let alpha = POPBasicAnimation.init(propertyNamed: kPOPLayerOpacity)
        alpha?.fromValue = 0.6
        alpha?.toValue = 0.6
        alpha?.beginTime = CACurrentMediaTime()
        alpha?.duration = 0.25
        alpha?.timingFunction = CAMediaTimingFunction.init(name: CAMediaTimingFunctionName.easeOut)
        alpha?.removedOnCompletion = true
        
        view.layer.pop_add(scale, forKey: "scale")
        view.layer.pop_add(alpha, forKey: "alpha")
        
        scale?.completionBlock = ({ animation, finished in
            completion?()
        })
    }
}
```

続いて、MainTabBarController.swiftも編集します（一部省略）。 

```swift
// MainTabBarController.swift
import UIKit
import ESTabBarController

class MainTabBarController: ESTabBarController {
    override func viewDidLoad() {
        super.viewDidLoad()
    }
    
    required init?(coder aDecoder: NSCoder) {
        super.init(coder: aDecoder)
        
        // (省略)
        
        // 変更
        let v2 = UIStoryboard(name: "Second", bundle: nil).instantiateInitialViewController()
        v2?.tabBarItem = ESTabBarItem.init(TabBarCenterContentView(), title: "Find", image: UIImage(named: "photo_verybig"), selectedImage: UIImage(named: "photo_verybig_1"), tag: 2)
        v2?.title = "Photo"
        
        // (省略）
        
        // 追加
        self.shouldHijackHandler = { tabbarController, viewController, index in
            if index == 1 {
                return true
            }
            return false
        }
        self.didHijackHandler = { [weak self] tabbarController, viewController, index in
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) {
                let alertController = UIAlertController.init(title: nil, message: nil, preferredStyle: .actionSheet)
                let takePhotoAction = UIAlertAction(title: "Take a photo", style: .default, handler: nil)
                alertController.addAction(takePhotoAction)
                let selectFromAlbumAction = UIAlertAction(title: "Select from album", style: .default, handler: nil)
                alertController.addAction(selectFromAlbumAction)
                let cancelAction = UIAlertAction(title: "Cancel", style: .cancel, handler: nil)
                alertController.addAction(cancelAction)
                self?.present(alertController, animated: true, completion: nil)
            }
        }
    }
}
```

真ん中の要素であるv2のcontentViewを先程作成した「TabBarCenterContentView」に変更し、画像も大きいサイズのものを設定しています。 

また、hijackHandlerを設定し、真ん中の要素をタップしたときの動作をオーバーライドしています。今回はAlertActionを表示する動作となっています。

 これで、真ん中が大きく表示されるタブの作成が完了です。 

## **おわりに**

気が向いたらここからさらに画面遷移してCoreDataにデータを追加してTableViewに反映させるところまで記事していきたいと思います。

 [1]: https://github.com/eggswift/ESTabBarController
