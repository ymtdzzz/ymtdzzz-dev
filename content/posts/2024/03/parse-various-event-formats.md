---
title: Lambda（Golang）でイベントデータをいい感じにパースする
date: 2024-03-21
tags:
 - Go
 - Lambda
 - AWS
published: true
category: Programming
---

# Table of Contents


# はじめに


Lambdaで色々なイベントソース（SQS, SNS, EventBridge etc.）からのデータをハンドリングする必要があり、各サービス固有の差分を吸収して欲しいデータを取得する処理を実装する機会があったのでメモしておきます。


ベースはこちらの記事を参考にしています。


[https://medium.com/@robert.bruce.cm/handling-multiple-aws-lambda-events-types-with-go-34e35426b724](https://medium.com/@robert.bruce.cm/handling-multiple-aws-lambda-events-types-with-go-34e35426b724)


※ほぼこちらのロジックを流用しつつジェネリクスで少し抽象度を高めただけです


# コード


コードの全文はこちらです


[https://github.com/ymtdzzz/lambda-event-parser](https://github.com/ymtdzzz/lambda-event-parser)


主要な処理をピックアップしてご紹介します。


## 実装


### Event


まずはLambda handlerでハンドリングするEventのstructを定義しておきます。


```go
// Event incoming event
type Event[T any] struct {
	Message *T
}
```


欲しいデータは何らかのイベントソースの中身になるので、こちらは利用側が自由に設定できます。よって`any`型を取るジェネリクスとします。


### UnmarshalJSON()


Lambda handler側で暗黙的に呼び出される、先ほどのEvent receiverを持つ関数です。


```go
func (e *Event[T]) UnmarshalJSON(v []byte) error {
	et, err := e.getEventType(v)
	if err != nil {
		return err
	}
	switch et {
	case sqsEventType:
		sqsEvent := &events.SQSEvent{}
		err := json.Unmarshal(v, sqsEvent)
		if err != nil && len(sqsEvent.Records) == 0 {
			return errors.Wrap(err, "failed to unmarshal sqs event")
		}
		var msg T
		err = json.Unmarshal([]byte(sqsEvent.Records[0].Body), &msg)
		if err != nil {
			return errors.Wrap(err, "failed to unmarshal sqs event body")
		}
		e.Message = &msg
		return nil

	case snsEventType:
		snsEvent := &events.SNSEvent{}
		err = json.Unmarshal(v, snsEvent)
		if err != nil && len(snsEvent.Records) == 0 {
			return errors.Wrap(err, "failed to unmarshal sns event")
		}
		var msg T
		err = json.Unmarshal([]byte(snsEvent.Records[0].SNS.Message), &msg)
		if err != nil {
			return errors.Wrap(err, "failed to unmarshal sns event body")
		}
		e.Message = &msg
		return nil

	case eventBridgeEventType:
		eventBridgeEvent := &events.EventBridgeEvent{}
		err := json.Unmarshal(v, eventBridgeEvent)
		if err != nil {
			return errors.Wrap(err, "failed to unmarshal event bridge event")
		}
		var msg T
		err = json.Unmarshal([]byte(eventBridgeEvent.Detail), &msg)
		if err != nil {
			return errors.Wrap(err, "failed to unmarshal event bridge event body")
		}
		e.Message = &msg
		return nil

	case unknownEventType:
		fmt.Printf("unknown event type: %s\n", string(v))
		return nil
	}

	return nil
}
```


始めに、後述する`getEventType()`でイベントの種類を特定し、あとはそれぞれのイベントのフォーマット毎に、データの中身が存在するfieldをunmarshalするだけです。


どのフォーマットであっても、基本的に欲しいデータは同じなのでそこはジェネリクスで抽象化することで、この関数の呼び出し側はイベントソースに関わらず欲しいデータが取得できるようにしています。


### getEventType()


こちらの実装は参考記事とほぼ同じです。


```go
func (event *Event[T]) getEventType(data []byte) (eventType, error) {
	temp := make(map[string]interface{})
	if err := json.Unmarshal(data, &temp); err != nil {
		return unknownEventType, err
	}

	if source, ok := temp["source"].(string); ok && source == "aws.events" {
		return eventBridgeEventType, nil
	}
	recordsList, _ := temp["Records"].([]interface{})
	record, _ := recordsList[0].(map[string]interface{})

	var eventSource string

	if es, ok := record["EventSource"]; ok {
		eventSource = es.(string)
	} else if es, ok := record["eventSource"]; ok {
		eventSource = es.(string)
	}

	switch eventSource {
	case "aws:sqs":
		return sqsEventType, nil
	case "aws:sns":
		return snsEventType, nil
	}

	return unknownEventType, nil
}
```


例えばSQSやSNSの場合、[AWSのドキュメント](https://docs.aws.amazon.com/ja_jp/lambda/latest/dg/with-sqs.html#example-standard-queue-message-event)より`Records`配列の`index 0`のデータを取得し、その`EventSource` or `eventSource` キーを見ることでイベントソースを判別することができます（Recordsは一つだけを前提としている）。


ここは結構泥臭く書く必要があります。また、`aws:sqs`といった定数についてもGoのAWS SDKだと見当たらなかったのでハードコーディングしています。


## 使用例


例えば別のアプリケーションから下記の構造でデータを生成していたとします。


```json
{
    "message": "test message",
    "user_ids": [
        10,
        123
    ]
}
```


パース側では対応するstructを定義しておきます。


```go
type MyEvent struct {
	Message string `json:"message"`
	UserIDs []int  `json:"user_ids"`
}
```


`UnmarshalJSON()`を呼び出し、パースします。


```go
data := []byte(`...`) // 渡ってきたデータ
event := &Event[MyEvent]{}
if err := got.UnmarshalJSON(data); err != nil {
	// error handling
}
// パースした中身を取り出す
msg := event.Message
```


詳細はテストコードをご参照下さい。


# さいごに


ジェネリクスも使いすぎると複雑度が増しますが、割と使いどころとしてカチッとハマった事例だと思ったので紹介させていただきました。


誰かの参考になりましたら幸いです。

