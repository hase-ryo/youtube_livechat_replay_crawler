# youtube_livechat_replay_crawler

YoutubeのVideoIdをキーにしてライブチャットをクローリングして取得、GCSに格納します
Pub/Subをトリガーにして起動します
Cloud Functionでの動作を想定しています


# 引数

## data

PubsubMessageの形式で受け取ります。
https://cloud.google.com/pubsub/docs/reference/rest/v1/PubsubMessage?hl=ja

attributeに以下二つの指定が必要です

* channel_id
* video_id

## context

特に使いません

# 環境変数

.envに記載してください

## SERVICE_ACCOUNT_CREDENTIAL_FILE

ローカルで動作させる場合はGCSのread, write権限をもつサービスアカウントのCredential fileが必要です。
credential file.jsonはsecret/配下においてください。
Cloud Functionで動作させる場合はデフォルトのサービスアカウントから認証情報を取得できるので不要です

## GCS_BUCKET_NAME

指定してください


# 注意事項 

チャットが多すぎるとCloud Functionの最大動作時間540秒を超えるかもしれません
その場合はローカルでの実行をおすすめします
