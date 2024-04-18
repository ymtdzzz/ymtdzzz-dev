---
title: Terraformの配列を分割する
date: 2024-04-18
tags:
 - Terraform
published: true
category: Programming
---

例えばremote stateとかから引っ張ってきた何かのリストがあったとして


```text
hoge = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]
```


それを10個ずつとかの配列に分割したい場合


```text
 output = [
     [
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "10",
     ],
     [
        "11",
        "12",
     ],
  ]
```


いつ使うんだよっていう話なんですが、GCPのCloud Armorで設定できる許可IPが1ルールあたり10個という制限があり、たまーにやりたくなります。


だいぶ黒魔術的な感じになってしまいますが、最終的に下記のようなコードを書きました。


```text
per_nums = 10 // 配列毎の最大要素数
input       = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]
array_nums = ceil(length(local.input) / local.per_nums)
arr         = slice(local.input, 0, local.array_nums) // ループ用配列（ループ回数とindex取得用にのみ使用）
last_idx    = length(local.input)
result = [
  for i, v in local.arr :
  slice(
    local.input,
    i * local.per_nums,
    min(i * local.per_nums + local.per_nums, local.last_idx),
  )
]
```


`array_nums`が分割後の配列数で、ループで該当するindexを指定してinputからsliceを生成して詰めています。


最後の`min()`でindex out of rangeを防止してきちんと最後の要素まで取り出せるようにしています。


```text
min(i * local.per_nums + local.per_nums, local.last_idx),
```

