from dotenv import load_dotenv
from google.cloud import storage as gcs
import os
import platform
import json
import base64
import sys
from google.cloud import pubsub_v1
from gcs_wrapper import gcs_wrapper

if platform.system() == 'Darwin':
    # run locally
    load_dotenv('.env')

bucket_name_in = os.environ.get("GCS_BUCKET_NAME_IN")
bucket_name_out = os.environ.get("GCS_BUCKET_NAME_OUT")
pubsub_topic = os.environ.get("PUBSUB_TOPIC")
project_id = os.environ.get("PROJECT_ID")

def check_chatlog_exist(channel_id):
    videofile_name = 'videos_v2/videolist' + channel_id + '.json'
    videos = gcs_wrapper.get_gcs_file_to_dictlist(bucket_name_in, videofile_name)
    all_video_ids = []
    for video in videos:
        all_video_ids.append(video['video_id'])

    prefix = channel_id + '/'
    chatlog_list = gcs_wrapper.get_gcs_files(bucket_name_out, prefix)
    clist = []
    for chatlog in chatlog_list:
        clist.append(chatlog.split('/')[1])
    video_ids = list(set(clist))

    result = []
    for video_id in all_video_ids:
        if not video_id in video_ids:
            result.append(video_id)

    print(channel_id + " found " + ("%03d" % len(result)) + " untouched videos")

    return(result)

def main(data, context):
    print(data)
    filename = data['name']
    if filename.split('/')[0] == 'videos_v2':
        channel_id = filename.split('/')[1].replace('videolist','').replace('.json','')
        untouched_video_ids = check_chatlog_exist(channel_id)

        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(project_id, pubsub_topic)
        for video_id in untouched_video_ids:
            future = publisher.publish(topic_path, "untouched_video_id".encode('utf-8'), channel_id=channel_id, video_id=video_id)

            print(video_id + " Pub/Sub publish result " + future.result())

if __name__ == '__main__':
    channel_id = sys.argv[1]
    untouched_video_ids = check_chatlog_exist(channel_id)
    print(untouched_video_ids)
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, pubsub_topic)
    for video_id in untouched_video_ids:
        future = publisher.publish(topic_path, "untouched_video_id".encode('utf-8'), channel_id=channel_id, video_id=video_id)
        print(video_id + " Pub/Sub publish result " + future.result())

