---
title: "Storybook に noarmalize.css を適用する"
date: 2020-05-14
tags:
  - "storybook"
  - "react"
  - "css"
published: True
category: Programming
---

## Storybook に normalize.css を適用する

`.storybook/config.js`に下記の通り import 文を記述します。

```js
import '!style-loader!css-loader!sass-loader!../src/styles/normalize.css';
```

現場からは以上です！！
