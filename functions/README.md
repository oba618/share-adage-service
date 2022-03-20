# #格言共有(AWS-Python)

座右の銘とそれにまつわるエピソードの共有が出来ます。

## 概要

#格言共有のバックエンド側のレポジトリです。AWS、ServerlessFramework、pythonを使用して作成しています。

[フロント側はこちら](https://github.com/oba618/docker-flask)

## 構築環境

- AWS
  - APIGateway
  - Lambda
  - DynamoDB
  - Cognito
- ServerlessFamework: 2.72.1
- python: 3.8

## 設置ページ

[#格言共有](https://share-adage-service.herokuapp.com/)

## 機能一覧(functions)

- ユーザ関連(user.py)
  - ユーザ登録
  - ユーザ検証（メール）
  - ユーザログイン
  - ユーザログアウト
  - ユーザ参照
  - ユーザ更新
  - ユーザ削除

- 格言関連(adage.py)
  - 格言登録
  - 格言参照
  - 格言登録
  - 格言削除

- エピソード関連(episode.py)
  - エピソード登録
  - エピソード参照
  - エピソード更新
  - エピソード削除

- いいね関連(heart.py)
  - いいね登録（ポイント追加）
  - いいね登録（履歴追加）

## Author

[twitter](https://twitter.com/oba618)
