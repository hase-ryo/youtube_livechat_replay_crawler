# untouched_video_checker

Identify videos that have not been stored chat log.
Compare the GCS file list with the list of publicly available videos.
Send the ID of the identified video to Google Cloud Pub/Sub.

## Requirement

### python packages

`pip install -r requirements.txt`

### Environment variable

Specify an environment variable in `.env.yaml` if you want to run it with Google Cloud Function or `.env` if you want to run it locally.

#### GCS_BUCKET_NAME_OUT

Specify bucket name of your GCS bucket which stores chat log file.

#### GCS_BUCKET_NAME_IN

Specify bucket name of your GCS bucket which stores video list of specified channel.

#### PUBSUB_TOPIC

Specify the Pub/Sub topic name to publish the video_id .

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

`check_chatlog_exist` function compares both the chat log files and list of video_id.
If the video_id is not found in chat log files, it will be returned as a list.
`main` function send the video IDs to the Pub/Sub topic.
If you don't need the Pub/Sub to run locally, please rewrite it to work.
