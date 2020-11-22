# channel_video_list

Get a list of publicly available videos from the Youtube Data API.
The argument is a Channel ID.
Place the retrieved list in Google Cloud Storage.

## Requirement

### python packages

`pip install -r requirements.txt`

### Environment variable

Specify an environment variable in `.env.yaml` if you want to run it with Google Cloud Function or `.env` if you want to run it locally.

#### YOUTUBE_DATA_API_KEY

Specify your key of YOUTUBE DATA API.

#### GCS_BUCKET_NAME

Specify URI of your GCS bucket.

#### GOOGLE_APPLICATION_CREDENTIALS (local run only)

Specify credential file of service account as json format.
See https://cloud.google.com/docs/authentication/getting-started

### gcs_wrapper

Sub-module for GCS operation.

`git submodule add https://github.com/hase-ryo/gcs_wrapper.git`

### Channels.json

Prepare a pair of Channel ID and Channel name as json to give the arguments easily.

Example:
```
{"name": "World Greatest Youtuber", "channel_id": "UC123456789"}
```

## Deploy to Google Cloud Function

run `./deploy.sh`

## Notes

`get_videos` function requests Youtube Data API with channel_id.
(The channel_id can be identified from the URL of the Youtube channel.)

Get list of video_id from Search.list() API.
And then, get published time of video, title, and duration time from Videos,list() API.
