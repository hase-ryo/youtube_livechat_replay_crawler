from flask import escape
from apiclient.discovery import build
from dotenv import load_dotenv
import platform
import json
import sys
import os
import numpy
import math
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

def get_videos(channel_id):
    # 動画ID一覧を取得
    # 動画数が500を超えるとvideos.listでは取得できない
    # quota消費が多いので注意
    if channel_id is None:
        print("Must specify channel_id")
        return(None)

    youtube = get_youtube_client()

    # channels.listからupload_idを取得

    channels_response = youtube.channels().list(
            id = channel_id,
            part = 'contentDetails',
            fields = 'items(contentDetails(relatedPlaylists(uploads)))',
            maxResults = 1
            ).execute()

    uploads_id = channels_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    print(channel_id + " upload id = " + uploads_id)

    # playlistsitems.listからvideo_idを取得

    nextPagetoken = None
    nextpagetoken = None
    videos = []
    while True:
        if nextPagetoken != None:
            nextpagetoken = nextPagetoken

        playlist_response = youtube.playlistItems().list(
                playlistId = uploads_id,
                part = 'snippet',
                fields = 'nextPageToken, items(snippet(resourceId))',
                maxResults = 50,
                pageToken = nextpagetoken
                ).execute()
        for playlist_result in playlist_response.get('items', []):
            if playlist_result['snippet']['resourceId']['kind'] == 'youtube#video':
                videos.append(playlist_result['snippet']['resourceId']['videoId'])

        try:
            nextPagetoken =  playlist_response["nextPageToken"]
        except:
            break

    print(channel_id + " contains " + ("%03d" % len(videos)) + " videos")
    return(videos)

def get_videoinfos(videos):
    # viode_idのlistを受け取り詳細を取得する

    if len(videos) == 0:
        return([])
    if len(videos) < 50:
        iterate_num = 1
    else:
        iterate_num = math.floor(len(videos) / 50) + 1

    youtube = get_youtube_client()
    video_infos = []
    video_lists = []
    for video_array in numpy.array_split(videos, iterate_num):
        video_lists.append(video_array.tolist())

    for video_list in video_lists:
        video_ids = ",".join(video_list)
        videos_response = youtube.videos().list(
                part = 'snippet, contentDetails',
                id = video_ids
                ).execute()
        for video_result in videos_response.get('items', []):
            videoinfo = {}
            videoinfo['video_id'] = video_result['id']
            videoinfo['channel_id'] = video_result['snippet']['channelId']
            videoinfo['published_at'] = video_result['snippet']['publishedAt']
            videoinfo['title'] = video_result['snippet']['title']
            videoinfo['duration'] = video_result['contentDetails']['duration']
            video_infos.append(videoinfo)

    return(video_infos)

def parse_request(request, key):
    request_json = request.get_json(silent=True)
    request_args = request.args
    value = None
    if request_json and key in request_json:
        value = request_json[key]
    elif request_args and key in request_args:
        value = request_args[key]

    return(value)

def channel_name_to_id(name):
    # 名称をchannel_idに変換させる
    channel_id = None
    channels = gcs_wrapper.get_gcs_file_to_dictlist(bucket_name, 'channels.json')
    for channel in channels:
        if channel['name'] == name:
            channel_id = channel['channel_id']
            print(channel)

    return(channel_id)

def get_completed_videos(channel_id):
    # GCSに保存した動画一覧を読み出す
    completed_videoinfos = []
    file_path = 'videos_v2/videolist' + channel_id + '.json'
    if gcs_wrapper.check_gcs_file_exists(bucket_name, file_path):
        completed_videoinfos = gcs_wrapper.get_gcs_file_to_dictlist(bucket_name, file_path)
    return(completed_videoinfos)

def get_new_videos(videos, completed_videos):
    # 取得済の動画と動画一覧を比較して差分を返す

    diff_videos = list(set(videos) - set(completed_videos))
    print("new videos = " + ("%03d" % len(diff_videos)))
    return(diff_videos)

def main(request):
    name = parse_request(request, 'name')
    full_retry = parse_request(request, 'full_refresh')
    channels = gcs_wrapper.get_gcs_file_to_dictlist(bucket_name, 'channels.json')

    channel_id = channel_name_to_id(name)

    if not channel_id:
        return

    videos = get_videos(channel_id)
    completed_videoinfos = get_completed_videos(channel_id)

    if full_retry == "yes":
        print("Re-scan all videos " + name + " " + channel_id)
        completed_videoinfos = []

    comp_videos = []
    for videoinfo in completed_videoinfos:
        comp_videos.append(videoinfo['video_id'])
    new_videos = get_new_videos(videos, comp_videos)
    new_videoinfos = get_videoinfos(new_videos)

    completed_videoinfos.extend(new_videoinfos)

    gcs_wrapper.upload_gcs_file_from_dictlist(bucket_name, file_path,completed_videoinfos)
    print("Success to get and upload videos of " + escape(name))

if __name__ == '__main__':
    name = sys.argv[1]
    full_retry = sys.argv[2]
    channel_id = channel_name_to_id(name)
    videos = get_videos(channel_id)
    completed_videoinfos = get_completed_videos(channel_id)
    comp_videos = []
    if full_refresh == "yes":
        print("Re-scan all videos " + name + " " + channel_id)
        completed_videoinfos = []
    for videoinfo in completed_videoinfos:
        comp_videos.append(videoinfo['video_id'])
    new_videos = get_new_videos(videos, comp_videos)
    new_videoinfos = get_videoinfos(new_videos)
    completed_videoinfos.extend(new_videoinfos)
    print(len(completed_videoinfos))


