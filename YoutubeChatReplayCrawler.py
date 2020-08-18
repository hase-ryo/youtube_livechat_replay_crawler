#!/usr/bin/env python3

from bs4 import BeautifulSoup
import requests
import re
import sys
import json
from retry import retry


class ContinuationURLNotFound(Exception):
    pass

class LiveChatReplayDisabled(Exception):
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
                    return(json.loads(line.strip()[len('window["ytInitialData"] = '):-1]))

def get_continuation(ytInitialData):
    continuation = ytInitialData['continuationContents']['liveChatContinuation']['continuations'][0].get('liveChatReplayContinuationData', {}).get('continuation')
    return(continuation)

def check_livechat_replay_disable(ytInitialData):
    conversationBarRenderer = ytInitialData['contents']['twoColumnWatchNextResults']['conversationBar'].get('conversationBarRenderer', {})
    if conversationBarRenderer:
        if conversationBarRenderer['availabilityMessage']['messageRenderer']['text']['runs'][0]['text'] == 'この動画ではチャットのリプレイを利用できません。':
            return(True)

@retry(ContinuationURLNotFound, tries=3, delay=1)
def get_initial_continuation(target_url,session):

    ytInitialData = get_ytInitialData(target_url, session)

    if check_livechat_replay_disable(ytInitialData):
        print("LiveChat Replay is disable")
        raise LiveChatReplayDisabled

    continue_dict = {}
    continuations = ytInitialData['contents']['twoColumnWatchNextResults']['conversationBar']['liveChatRenderer']['header']['liveChatHeaderRenderer']['viewSelector']['sortFilterSubMenuRenderer']['subMenuItems']
    for continuation in continuations:
        continue_dict[continuation['title']] = continuation['continuation']['reloadContinuationData']['continuation']

    continue_url = continue_dict.get('Live chat repalay')
    if not continue_url:
        continue_url = continue_dict.get('上位のチャットのリプレイ')

    if not continue_url:
        continue_url = continue_dict.get('チャットのリプレイ')

    if not continue_url:
        continue_url = ytInitialData["contents"]["twoColumnWatchNextResults"]["conversationBar"]["liveChatRenderer"]["continuations"][0].get("reloadContinuationData", {}).get("continuation")

    if not continue_url:
        raise ContinuationURLNotFound

    return(continue_url)

def convert_chatreplay(renderer):
    chatlog = {}

    chatlog['user'] = renderer['authorName']['simpleText']
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
                    content += runs['emoji']['shortcuts'][0]
    chatlog['text'] = content

    if 'purchaseAmountText' in renderer:
        chatlog['purchaseAmount'] = renderer['purchaseAmountText']['simpleText']
        chatlog['type'] = 'SUPERCHAT'
    else:
        chatlog['purchaseAmount'] = ""
        chatlog['type'] = 'NORMALCHAT'

    return(chatlog)

def get_chat_replay_data(video_id):
    youtube_url = "https://www.youtube.com/watch?v="
    target_url = youtube_url + video_id
    continuation_prefix = "https://www.youtube.com/live_chat_replay?continuation="
    result = []
    session = requests.Session()
    continuation = ""

    try:
        continuation = get_initial_continuation(target_url, session)
    except LiveChatReplayDisabled:
        print(video_id + " is disabled Livechat replay")
        raise LiveChatReplayDisabled
    except ContinuationURLNotFound:
        print(video_id + " can not find continuation url")
        raise ContinuationURLNotFound
    except Exception:
        print("Unexpected error:" + str(sys.exc_info()[0]))

    count = 1
    pagecount = 1
    while(1):
        if not continuation:
            break

        try:
            ytInitialData = get_ytInitialData(continuation_prefix + continuation, session)
            if not 'actions' in ytInitialData['continuationContents']['liveChatContinuation']:
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
            break
        except SyntaxError as e:
            print("SyntaxError")
            print(e)
            break
        except KeyboardInterrupt:
            break
        except Exception as e:
            print("Unexpected error:" + str(sys.exc_info()[0]))
            print(e)
            break

    print(video_id + " found " + ("%05d" % pagecount) + " pages")
    return(result)
