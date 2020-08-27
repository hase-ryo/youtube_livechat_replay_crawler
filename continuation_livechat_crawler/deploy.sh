#!/bin/sh

set -a; source .env; set +a;

gcloud functions deploy continuation_livechat_crawler --entry-point main --runtime python37 --trigger-topic $PUBSUB_TOPIC --env-vars-file .env.yaml --timeout 540
