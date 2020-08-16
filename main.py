import platform
import json
import sys
import os
import time
import base64
from dotenv import load_dotenv
from YoutubeChatReplayCrawler import get_chat_replay_data, LiveChatReplayDisabled, ContinuationURLNotFound
from gcs_wrapper import gcs_wrapper
from google.cloud import storage as gcs


if platform.system() == 'Darwin':
    # run locally
    load_dotenv('.env')

bucket_name = os.environ.get("GCS_BUCKET_NAME")

def main(event, context):
    # Pub/subからトリガーを受け取る
    start = time.time()
    data = base64.b64decode(event['data']).decode('utf-8')
    if data == 'untouched_video_id':
        video_id = event['attributes']['video_id']
        channel_id = event['attributes']['channel_id']
        if gcs_wrapper.check_gcs_file_exists(bucket_name, channel_id + '/livechatconvertlog' + video_id + '.json'):
            print(video_id + " is already exist. End")
        else:
            try:
                comment_data = get_chat_replay_data(video_id)
            except LiveChatReplayDisabled:
                print(video_id + " is disabled Livechat replay, create blank list")
                comment_data = []
            if comment_data:
                gcs_wrapper.upload_gcs_file_from_dictlist(bucket_name, channel_id + '/livechatconvertlog' + video_id + '.json', comment_data)

    elapsed_time = time.time() - start
    print("{0}".format(elapsed_time) + " sec")

if __name__ == '__main__':
    # 手動で起動した場合はvideo_idのリストを受け取って直接取りにいく
    # 既存かどうかも気にせず再取得
    start = time.time()
    channel_id = sys.argv[1]
    video_ids = sys.argv[2].split(',')
    for video_id in video_ids:
        try:
            comment_data = get_chat_replay_data(video_id)
        except LiveChatReplayDisabled:
            print(video_id + " is disabled Livechat replay, create blank list")
            comment_data = []
        if comment_data:
            gcs_wrapper.upload_gcs_file_from_dictlist(bucket_name, channel_id + '/livechatconvertlog' + video_id + '.json', comment_data)
    elapsed_time = time.time() - start
    print("{0}".format(elapsed_time) + " sec")


