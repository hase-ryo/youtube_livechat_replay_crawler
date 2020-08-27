#!/bin/sh

set -a; source .env; set +a;

gcloud functions deploy youtube_untouched_video_checker --entry-point main --runtime python37 --trigger-bucket $GCS_BUCKET_NAME_IN --env-vars-file .env.yaml --timeout 180
