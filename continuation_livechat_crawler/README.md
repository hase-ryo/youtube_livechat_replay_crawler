# continuation_livechat_crawler

Get the chat log continuously.
The argument is the URL where the first chat log is stored.
Get 800 pages of chat logs.
If there is still a continuation, send the following URL to the Pub/Sub.
Finish when the rest is gone.

## Requirement

### python packages

`pip install -r requirements.txt`

### Environment variable

Specify an environment variable in `.env.yaml` if you want to run it with Google Cloud Function or `.env` if you want to run it locally.

#### GCS_BUCKET_NAME

Specify bucket name of your GCS bucket which stores chat log file.

#### PUBSUB_TOPIC

Specify the Pub/Sub topic name to publish/subscribe URL of chat log.

#### PROJECT_ID

Specify ID of your Google Cloud Platform.

#### GOOGLE_APPLICATION_CREDENTIALS (local run only)

Specify credential file of service account as json format.
See https://cloud.google.com/docs/authentication/getting-started

### gcs_wrapper

Sub-module for GCS operation.

`git submodule add https://github.com/hase-ryo/gcs_wrapper.git`

## Deploy to Google Cloud Function

run `./deploy.sh`

## Notes

`get_chat_replay_from_continuation` is core of this scripts.
Search and retrieve the `ytInitialData` block from HTTP source.
It contains chat replay log.
Decompose the data in json format and process and store it in chat log format.
Use it in combination with `initial_livechat_check` if it runs locally.
By increasing the limit of pagecount or making it infinite, you can get rid of the entire video chat log, even if you run it locally.
However, that case will take a long time.
