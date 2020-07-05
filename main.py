import platform
import json
import sys
import os
import time
import base64
from dotenv import load_dotenv
from YoutubeChatReplayCrawler import YoutubeChatReplayCrawler, chatReplayConverter
from google.cloud import storage as gcs


if platform.system() == 'Darwin':
    # run locally
    load_dotenv('.env')

bucket_name = os.environ.get("GCS_BUCKET_NAME")

def get_gcs_client():
    if platform.system() == 'Linux':
        # run at cloud
        client = gcs.Client()
    elif platform.system() == 'Darwin':
        # run locally
        load_dotenv('.env')
        client = gcs.Client.from_service_account_json(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))

    return(client)

def check_gcs_chatlog_exists(channel_id, video_id):
    file_path = channel_id + '/livechatconvertlog' + video_id + '.json'

    client = get_gcs_client()
    bucket = client.get_bucket(bucket_name)
    blob = bucket.get_blob(file_path)
    if blob is None:
        return('not exists')
    elif blob.size == 0:
        return('not exists')
    else:
        return('exists')

def upload_gcs_chatlog(result, channel_id, video_id):
    file_path = channel_id + '/livechatconvertlog' + video_id + '.json'

    client = get_gcs_client()
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(file_path)
    blob.upload_from_string('\n'.join(result))
    print("GCS upload success!!")

def main(event, context):
    # triggered by Pub/sub
    start = time.time()
    data = base64.b64decode(event['data']).decode('utf-8')
    if data == 'untouched_video_id':
        video_id = event['attributes']['video_id']
        channel_id = event['attributes']['channel_id']
        exist_check = check_gcs_chatlog_exists(channel_id, video_id)
        print(exist_check + " " + video_id)
        if exist_check == 'not exists':
            comment_data = YoutubeChatReplayCrawler.YoutubeChatReplayCrawler(video_id)
            if comment_data:
                result = chatReplayConverter.chatReplayConverter(comment_data, video_id)
                if result:
                    upload_gcs_chatlog(result, channel_id, video_id)

    elapsed_time = time.time() - start
    print("{0}".format(elapsed_time) + " sec")

if __name__ == '__main__':
    attributes = {}
    attributes['channel_id'] = sys.argv[1]
    attributes['video_id'] = sys.argv[2]
    event = {}
    event['attributes'] = attributes
    event['data'] = base64.b64encode('untouched_video_id'.encode('utf-8'))
    main(event, "")

