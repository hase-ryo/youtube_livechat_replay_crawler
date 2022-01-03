import platform
import json
import sys
import os
import time
import base64
from dotenv import load_dotenv
from gcs_wrapper import gcs_wrapper
from google.cloud import pubsub_v1
from bs4 import BeautifulSoup
import requests


if platform.system() == 'Darwin':
    # run locally
    load_dotenv('.env')

bucket_name = os.environ.get("GCS_BUCKET_NAME")
pubsub_topic = os.environ.get("PUBSUB_TOPIC")
project_id = os.environ.get("PROJECT_ID")

class RestrictedFromYoutube(Exception):
    pass

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
                        start_pos = line.strip().find('window["ytInitialData"]') + len('window["ytInitialData"] = ')
                        end_pos = len(';</script>') * -1
                        return(json.loads(line.strip()[start_pos:end_pos]))

    if 'Sorry for the interruption. We have been receiving a large volume of requests from your network.' in str(soup):
        print("restricted from Youtube (Rate limit)")
        raise RestrictedFromYoutube

    print("Cannot get ytInitialData")
    return(None)

def get_continuation(ytInitialData):
    continuation = ytInitialData['continuationContents']['liveChatContinuation']['continuations'][0].get('liveChatReplayContinuationData', {}).get('continuation')
    return(continuation)

def convert_chatreplay(renderer):
    chatlog = {}

    if 'authorName' in renderer:
        chatlog['user'] = renderer['authorName']['simpleText']
    else:
        chatlog['user'] = ""
    chatlog['timestampUsec'] = renderer['timestampUsec']
    chatlog['time'] = renderer['timestampText']['simpleText']

    if 'authorBadges' in renderer:
        chatlog['authorbadge'] = renderer['authorBadges'][0]['liveChatAuthorBadgeRenderer']['tooltip']
    else:
        chatlog['authorbadge'] = ""

    content = ""
    if 'message' in renderer:
        if 'simpleText' in renderer['message']:
            content = renderer['message']['simpleText']
        elif 'runs' in renderer['message']:
            for runs in renderer['message']['runs']:
                if 'text' in runs:
                    content += runs['text']
                if 'emoji' in runs:
                    is_custom_emoji = runs['emoji'].get('isCustomEmoji')
                    if is_custom_emoji:
                        content += ''.join(runs['emoji']['shortcuts'])
                    else:
                        content += runs['emoji']['emojiId']
    chatlog['text'] = content

    if 'purchaseAmountText' in renderer:
        chatlog['purchaseAmount'] = renderer['purchaseAmountText']['simpleText']
        chatlog['type'] = 'SUPERCHAT'
    else:
        chatlog['purchaseAmount'] = ""
        chatlog['type'] = 'NORMALCHAT'

    return(chatlog)

def get_chat_replay_from_continuation(video_id, continuation, pagecount_limit = 800, is_locally_run = False):
    count = 1
    pagecount = 1
    continuation_prefix = "https://www.youtube.com/live_chat_replay?continuation="
    session = requests.Session()
    result = []
    while(pagecount < pagecount_limit):
        if not continuation:
            print("continuation is None. maybe hit the last chat segment")
            break

        try:
            ytInitialData = get_ytInitialData(continuation_prefix + continuation, session)
            if not ytInitialData:
                print("video_id: " + video_id + " , continuation: " + continuation)
                continuation = None
                break

            if not 'actions' in ytInitialData['continuationContents']['liveChatContinuation']:
                continuation = None
                break
            for action in ytInitialData['continuationContents']['liveChatContinuation']['actions']:
                if not 'addChatItemAction' in action['replayChatItemAction']['actions'][0]:
                    continue
                chatlog = {}
                item = action['replayChatItemAction']['actions'][0]['addChatItemAction']['item']
                if 'liveChatTextMessageRenderer' in item:
                    chatlog = convert_chatreplay(item['liveChatTextMessageRenderer'])
                elif 'liveChatPaidMessageRenderer' in item:
                    chatlog = convert_chatreplay(item['liveChatPaidMessageRenderer'])

                if 'liveChatTextMessageRenderer' in item or 'liveChatPaidMessageRenderer' in item:
                    chatlog['video_id'] = video_id
                    chatlog['Chat_No'] = ("%05d" % count)
                    result.append(chatlog)
                    count += 1

            continuation = get_continuation(ytInitialData)
            pagecount += 1
            if is_locally_run:
                print('\rPage %d' % pagecount, end='')

        except requests.ConnectionError:
            print("Connection Error")
            continue
        except requests.HTTPError:
            print("HTTPError")
            break
        except requests.Timeout:
            print("Timeout")
            continue
        except requests.exceptions.RequestException as e:
            print(e)
            break
        except KeyError as e:
            print("KeyError")
            print(e)
            print(item['liveChatTextMessageRenderer'])
            break
        except SyntaxError as e:
            print("SyntaxError")
            print(e)
            break
        except KeyboardInterrupt:
            break
        except RestrictedFromYoutube:
            print("Restricted from Youtube, Rate limit")
            break
        except Exception as e:
            print("Unexpected error:" + str(sys.exc_info()[0]))
            print(e)
            break

    print(video_id + " found " + ("%03d" % pagecount) + " pages")
    return(result, continuation)

def main(event, context):
    start = time.time()
    data = base64.b64decode(event['data']).decode('utf-8')
    if data == 'continuation':
        continuation = event['attributes']['continuation']
        video_id = event['attributes']['video_id']
        channel_id = event['attributes']['channel_id']
        filepath = channel_id + '/' + video_id + '/' + continuation + '.json'
        print(continuation)
        comment_data, new_continuation = get_chat_replay_from_continuation(video_id, continuation)
        if comment_data:
            gcs_wrapper.upload_gcs_file_from_dictlist(bucket_name, filepath, comment_data)
        if new_continuation:
            if continuation != new_continuation:
                publisher = pubsub_v1.PublisherClient()
                topic_path = publisher.topic_path(project_id, pubsub_topic)
                future = publisher.publish(topic_path, "continuation".encode('utf-8'), continuation=new_continuation, channel_id=channel_id, video_id=video_id)

    elapsed_time = time.time() - start
    print("{0}".format(elapsed_time) + " sec")

if __name__ == '__main__':
    start = time.time()
    channel_id = sys.argv[1]
    video_id = sys.argv[2]
    continuation = sys.argv[3]
    filepath = channel_id + '/' + video_id + '/' + continuation + '.json'
    comment_data, new_continuation = get_chat_replay_from_continuation(video_id, continuation)
    if comment_data:
        gcs_wrapper.upload_gcs_file_from_dictlist(bucket_name, filepath, comment_data)
        continuation = new_continuation

    elapsed_time = time.time() - start
    print("{0}".format(elapsed_time) + " sec")


