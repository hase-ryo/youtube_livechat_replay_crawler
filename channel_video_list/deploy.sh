#!/bin/sh

gcloud functions deploy youtube_channel_video_list --entry-point main --runtime python37 --trigger-http --env-vars-file .env.yaml --allow-unauthenticated --timeout 180
