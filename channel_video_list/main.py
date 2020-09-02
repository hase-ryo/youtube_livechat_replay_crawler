from flask import escape
from apiclient.discovery import build
from dotenv import load_dotenv
import platform
import json
import sys
import os
from unittest.mock import Mock
from oauth2client.client import GoogleCredentials
from httplib2 import Http
from datetime import datetime
from gcs_wrapper import gcs_wrapper

if platform.system() == 'Darwin':
    # run locally
    load_dotenv('.env')

bucket_name = os.environ.get("GCS_BUCKET_NAME")

def get_youtube_client():
    api_key = os.environ.get("YOUTUBE_DATA_API_KEY")
    if platform.system() == 'Linux':
        # run at cloud
        credentials = GoogleCredentials.get_application_default()
        client = build('youtube', 'v3', developerKey=api_key, http=credentials.authorize(Http()), cache_discovery=False)
    elif platform.system() == 'Darwin':
        # run locally
        client = build('youtube', 'v3', developerKey=api_key)
    return(client)

def get_videos(channel_id, border_time):
    if channel_id is None:
        print("Must specify channel_id")
        return(None)

    youtube = get_youtube_client()

    nextPagetoken = None
    nextpagetoken = None
    videos = []
    border = False
    # 動画Idの取得
    while True:
        if nextPagetoken != None:
            nextpagetoken = nextPagetoken

        search_response = youtube.search().list(
          part = 'id',
          channelId = channel_id,
          eventType = 'completed',
          type = 'video',
          maxResults = 50,
          order = 'date',
          pageToken = nextpagetoken
          ).execute()

        for search_result in search_response.get('items', []):
            if search_result['id']['kind'] == 'youtube#video':
                videoinfo = {}
                videoinfo['video_id'] = search_result['id']['videoId']
                videos_response = youtube.videos().list(
                        part = 'snippet, contentDetails',
                        id = videoinfo['video_id']
                        ).execute()
                for video_result in videos_response.get('items', []):
                    videoinfo['channel_id'] = video_result['snippet']['channelId']
                    videoinfo['published_at'] = video_result['snippet']['publishedAt']
                    videoinfo['title'] = video_result['snippet']['title']
                    videoinfo['duration'] = video_result['contentDetails']['duration']

                if border_time >= datetime.strptime(videoinfo['published_at'], '%Y-%m-%dT%H:%M:%SZ'):
                    border = True
                    break

                videos.append(videoinfo)

        if border:
            break

        try:
            nextPagetoken =  search_response["nextPageToken"]
        except:
            break

    return(videos)


def parse_request(request, key):
    request_json = request.get_json(silent=True)
    request_args = request.args
    value = None
    if request_json and key in request_json:
        value = request_json[key]
    elif request_args and key in request_args:
        value = request_args[key]

    return(value)


def main(request):
    name = parse_request(request, 'name')
    full_retry = parse_request(request, 'full_retry')
    max_published_at = datetime.strptime('2000-01-01T00:00:00Z', '%Y-%m-%dT%H:%M:%SZ')
    channels = gcs_wrapper.get_gcs_file_to_dictlist(bucket_name, 'channels.json')

    for channel in channels:
        if channel['name'] == name:
            channel_id = channel['channel_id']
            print(channel)

    if not channel_id:
        return
    file_path = 'videos_v2/videolist' + channel_id + '.json'

    if full_retry:
        videos = get_videos(channel_id, max_published_at)
    else:
        if gcs_wrapper.check_gcs_file_exists(bucket_name, file_path):
            videos = gcs_wrapper.get_gcs_file_to_dictlist(bucket_name, file_path)
            for videoinfo in videolist:
                if max_published_at < datetime.strptime(videoinfo['published_at'], '%Y-%m-%dT%H:%M:%SZ'):
                    max_published_at = datetime.strptime(videoinfo['published_at'], '%Y-%m-%dT%H:%M:%SZ')
        else:
            videos = []
        new_videos = get_videos(channel_id, max_published_at)
        videos.extend(new_videos)

    gcs_wrapper.upload_gcs_file_from_dictlist(bucket_name, file_path,videos)
    print("Success to get and upload videos of " + escape(name))

if __name__ == '__main__':
    name = sys.argv[1]
    full_retry = sys.argv[2]
    data = {'name': name, 'full_retry': full_retry}
    req = Mock(get_json=Mock(return_value=data), args=data)
    main(req)

