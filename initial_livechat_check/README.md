# initial_livechat_check

Get the HTTP source from the Youtube video page.
The arguments are channel id and video id.
Determines if a chat log exists.
Searches for URLs to be retrieved on a continuous basis.
If it exists, send it to the Pub/Sub.

## Requirement

### python packages

`pip install -r requirements.txt`

### Environment variable

Specify an environment variable in `.env.yaml` if you want to run it with Google Cloud Function or `.env` if you want to run it locally.

#### GCS_BUCKET_NAME

Specify bucket name of your GCS bucket which stores chat log file.

#### GCS_BUCKET_NAME_IN

Specify bucket name of your GCS bucket which stores video list of specified channel.

#### PUBSUB_TOPIC_IN

Specify the Pub/Sub topic name to subscribe video_id.

#### PUBSUB_TOPIC_OUT

Specify the Pub/Sub topic name to publish URL of chat log.

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

`get_initial_continuation` function retrieve HTTP source of Youtube video page.
You may not be able to find the chat log URL for various reasons.
Even if you are sure the chat log is valid.
If you are having trouble getting the chat log, check the HTTP source that beatufulsoup retrieved.

`check_initial_continuaion` function determine whether chat replay is avaiable or not.
If you are sure that the chat replay is invalid, it places blank.json in GCS.
