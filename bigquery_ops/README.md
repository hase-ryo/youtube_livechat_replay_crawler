# bigquery_ops

Loads the data stored in GCS to BigQuery.
It starts manually.
If the total number of chat logs is low compared to the video time, mark it as uncollected video.
Remove uncollected video.

## Requirement

### Environment variable

Specify an environment variable in `.env`

#### GCS_BUCKET_NAME

Specify bucket name of your GCS bucket which stores chat log file.

#### PROJECT_ID

Specify ID of your Google Cloud Platform.

#### GOOGLE_APPLICATION_CREDENTIALS (local run only)

Specify credential file of service account as json format.
See https://cloud.google.com/docs/authentication/getting-started

### gcs_wrapper

Sub-module for GCS operation.

`git submodule add https://github.com/hase-ryo/gcs_wrapper.git`

## Notes

`load_tables` is for loading files in GCS to BigQuery.
It loads both video list and chat log files.

`clean_lacked_log` removes the incomplete chat log file from the GCS.
Continuous chat log retrieval may rarely fail and finish the process without retrieving the last comment of the video.
Compare the length of the video with the timestamp in the chat log, and if the length of time obtained in the chat log is shorter, delete the log for that video.
