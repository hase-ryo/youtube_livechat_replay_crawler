#!/bin/sh

set -a; source .env; set +a;

gcloud functions deploy youtube_initial_livechat_check --entry-point main --runtime python37 --trigger-topic $PUBSUB_TOPIC_IN --env-vars-file .env.yaml --timeout 180
