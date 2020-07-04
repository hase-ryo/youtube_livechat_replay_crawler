import platform
import json
import sys
import os
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
        client = gcs.Client.from_service_account_json(os.environ.get("SERVICE_ACCOUNT_CREDENTIAL_FILE"))
    return(client)

def check_gcs_chatlog_exists(channel_id, video_id):
    file_path = channel_id + '/livechatconvertlog' + video_id + '.json'

    client = get_gcs_client()
    bucket = client.get_bucket(bucket_name)
    blob = bucket.get_blob(file_path)
    if blob is None:
        return(False)
    elif blob.size == 0:
        return(False)
    else:
        return(True)

def upload_gcs_chatlog(result, channel_id, video_id):
    file_path = channel_id + '/livechatconvertlog' + video_id + '.json'

    client = get_gcs_client()
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(file_path)
    blob.upload_from_string('\n'.join(result))
    print("GCS upload success!!")

def main(data, context):
    video_id = data['attributes']['video_id']
    channel_id = data['attributes']['channel_id']
    comment_data = YoutubeChatReplayCrawler.YoutubeChatReplayCrawler(video_id)
    if comment_data:
        result = chatReplayConverter.chatReplayConverter(comment_data, video_id)
        if result:
            upload_gcs_chatlog(result, channel_id, video_id)

if __name__ == '__main__':
    attributes = {}
    attributes['channel_id'] = sys.argv[1]
    attributes['video_id'] = sys.argv[2]
    data = {}
    data['attributes'] = attributes
    main(data, "")

