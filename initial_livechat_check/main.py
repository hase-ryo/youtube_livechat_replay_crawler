import platform
import json
import sys
import os
import base64
from dotenv import load_dotenv
from gcs_wrapper import gcs_wrapper
from retry import retry
from bs4 import BeautifulSoup
from google.cloud import pubsub_v1
import requests

if platform.system() == 'Darwin':
    # run locally
    load_dotenv('.env')

bucket_name = os.environ.get("GCS_BUCKET_NAME")
bucket_name_in = os.environ.get("GCS_BUCKET_NAME_IN")
pubsub_topic = os.environ.get("PUBSUB_TOPIC_OUT")
project_id = os.environ.get("PROJECT_ID")

class ContinuationURLNotFound(Exception):
    pass

class LiveChatReplayDisabled(Exception):
    pass

class RestrictedFromYoutube(Exception):
    pass

def check_chatlog_exist(channel_id):
    videofile_name = 'videos_v2/videolist' + channel_id + '.json'
    videos = gcs_wrapper.get_gcs_file_to_dictlist(bucket_name_in, videofile_name)
    all_video_ids = []
    for video in videos:
        all_video_ids.append(video['video_id'])

    prefix = channel_id + '/'
    chatlog_list = gcs_wrapper.get_gcs_files(bucket_name, prefix)
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

def get_ytInitialData(target_url, session):
    headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'}
    html = session.get(target_url, headers=headers)
    soup = BeautifulSoup(html.text, 'html.parser')
    for script in soup.find_all('script'):
        script_text = str(script)
        if 'ytInitialData' in script_text:
            for line in script_text.splitlines():
                if 'ytInitialData' in line:
                    if 'var ytInitialData =' in line:
                        st = line.strip().find('var ytInitialData =') + 19
                        return(json.loads(line.strip()[st:-10]))
                    if 'window["ytInitialData"] =' in line:
                        return(json.loads(line.strip()[len('window["ytInitialData"] = '):-1]))
#                    return(json.loads(line.strip()[len('window["ytInitialData"] = '):-1]))

    if 'Sorry for the interruption. We have been receiving a large volume of requests from your network.' in str(soup):
        print("restricted from Youtube (Rate limit)")
        raise RestrictedFromYoutube

    return(None)

def check_livechat_replay_disable(ytInitialData):
    conversationBar = ytInitialData['contents'].get('twoColumnWatchNextResults',{}).get('conversationBar', {})
    if conversationBar:
        conversationBarRenderer = conversationBar.get('conversationBarRenderer', {})
        if conversationBarRenderer:
            text = conversationBarRenderer.get('availabilityMessage',{}).get('messageRenderer',{}).get('text',{}).get('runs',[{}])[0].get('text')
            print(text)
            if text == 'この動画ではチャットのリプレイを利用できません。':
                return(True)
    else:
        return(True)

    return(False)

@retry(ContinuationURLNotFound, tries=2, delay=1)
def get_initial_continuation(target_url):
    print(target_url)
    session = requests.session()
    try:
        ytInitialData = get_ytInitialData(target_url, session)
    except RestrictedFromYoutube:
        return(None)


    if not ytInitialData:
        print("Cannot get ytInitialData")
        raise ContinuationURLNotFound

    if check_livechat_replay_disable(ytInitialData):
        print("LiveChat Replay is disable")
        raise LiveChatReplayDisabled

    continue_dict = {}
    try:
        continuations = ytInitialData['contents']['twoColumnWatchNextResults']['conversationBar']['liveChatRenderer']['header']['liveChatHeaderRenderer']['viewSelector']['sortFilterSubMenuRenderer']['subMenuItems']
        for continuation in continuations:
            continue_dict[continuation['title']] = continuation['continuation']['reloadContinuationData']['continuation']
    except KeyError:
        print("Cannot find continuation")

    continue_url = None
    if not continue_url:
        if continue_dict.get('上位のチャットのリプレイ'):
            continue_url = continue_dict.get('上位のチャットのリプレイ')
        if continue_dict.get('Top chat replay'):
            continue_url = continue_dict.get('Top chat replay')

    if not continue_url:
        if continue_dict.get('チャットのリプレイ'):
            continue_url = continue_dict.get('チャットのリプレイ')
        if continue_dict.get('Live chat replay'):
            continue_url = continue_dict.get('Live chat replay')

    if not continue_url:
        continue_url = ytInitialData["contents"]["twoColumnWatchNextResults"].get("conversationBar", {}).get("liveChatRenderer",{}).get("continuations",[{}])[0].get("reloadContinuationData", {}).get("continuation")

    if not continue_url:
        raise ContinuationURLNotFound

    return(continue_url)

def check_initial_continuation(channel_id, video_id):
    target_url = "https://www.youtube.com/watch?v=" + video_id
    file_prefix = channel_id + '/' + video_id + '/'
    if gcs_wrapper.check_gcs_file_exists(bucket_name, file_prefix):
        print(video_id + " is already exist. End")
        return(None)
    else:
        try:
            continuation = get_initial_continuation(target_url)
        except LiveChatReplayDisabled:
            print(video_id + " is disabled Livechat replay, create blank list")
            gcs_wrapper.upload_gcs_file_from_dictlist(bucket_name, file_prefix + 'blank.json', [{}])
            print(file_prefix + 'blank.json' + ' saved')
            return(None)
        except ContinuationURLNotFound:
            print(video_id + " can not find continuation url")
            return(None)
        except Exception as e:
            print(e)
        else:
            return(continuation)


def main(event, context):
    data = base64.b64decode(event['data']).decode('utf-8')
    if data == 'untouched_video_id':
        video_id = event['attributes']['video_id']
        channel_id = event['attributes']['channel_id']
        print(channel_id + '/' + video_id)
        continuation = check_initial_continuation(channel_id, video_id)
        if continuation:
            print(continuation)
            publisher = pubsub_v1.PublisherClient()
            topic_path = publisher.topic_path(project_id, pubsub_topic)
            future = publisher.publish(topic_path, "continuation".encode('utf-8'), continuation=continuation, channel_id=channel_id, video_id=video_id)
            print(video_id + " Pub/Sub publish result " + future.result())

if __name__ == '__main__':
    # channel_idとvideo_idのリストを受け取る
    channel_id = sys.argv[1]
    video_ids = sys.argv[2].split(',')
    for video_id in video_ids:
        continuation = check_initial_continuation(channel_id, video_id)
        if continuation:
            print(continuation)
            publisher = pubsub_v1.PublisherClient()
            topic_path = publisher.topic_path(project_id, pubsub_topic)
            future = publisher.publish(topic_path, "continuation".encode('utf-8'), continuation=continuation, channel_id=channel_id, video_id=video_id)
            print(video_id + " Pub/Sub publish result " + future.result())

