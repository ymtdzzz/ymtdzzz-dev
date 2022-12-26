---
title: Terraformで条件によってblock自体の出し分けをする方法
date: 2022-12-26
tags:
 - Terraform
published: true
category: Programming
---

例えばこの辺のリソースで、変数によって特定のruleの出し分けをしたい場合。


[https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_security_polic](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_security_policy)


variableの`is_maintenance`が`true`のときだけ`redirect` actionを設定したいとか。


```text
resource "google_compute_security_policy" "policy" {
    name = "my-policy"

  rule {
    action   = "allow"
    priority = "2147483647"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    description = "default rule"
  }

  // is_maintenanceがtrueのときだけ設定したい
  rule {
    action   = "redirect"
    priority = "1000"
		match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    
    redirect_option {
      type = "EXTERNAL_302"
      target = "https://example.com/maintenance"
    }
  }
}
```


その場合は、[dynamic block](https://developer.hashicorp.com/terraform/language/expressions/dynamic-blocks)の機能を使えば実現できます。


```text
// 省略
  dynamic rule {
    for_each = var.is_maintenance ? [1] : []
    content {
      action   = "redirect"
      priority = "1000"
		  match {
        versioned_expr = "SRC_IPS_V1"
        config {
          src_ip_ranges = ["*"]
        }
      }
    
      redirect_option {
        type = "EXTERNAL_302"
        target = "https://example.com/maintenance"
      }
    }
  }
```


この場合、`is_maintenance`が`true`ならruleを作成して、`false`ならrule丸ごと削ってくれます。


コードの可読性が下がるのでdynamic blockはあまり使わないようにしてましたが、こんな使い方もあったんですね。

