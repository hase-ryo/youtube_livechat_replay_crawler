#!/bin/sh

set -a; source .env; set +a;

gcloud functions deploy youtube_livechat_replay_crawler --entry-point main --runtime python37 --trigger-topic $PUBSUB_TOPIC --env-vars-file .env.yaml --timeout 540 --memory 512
