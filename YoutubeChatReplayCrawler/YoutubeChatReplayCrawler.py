#!/usr/bin/env python3

from bs4 import BeautifulSoup
import ast
import requests
import re
import sys
import json

def dict_str_to_dic(dict_str):
    # Capitalize booleans so JSON is valid Python dict.
    dict_str = dict_str.replace("false", "False")
    dict_str = dict_str.replace("true", "True")
    # Strip extra HTML from JSON.
    dict_str = re.sub(r'};.*\n.+<\/script>', '}', dict_str)

    # Correct some characters.
    dict_str = dict_str.rstrip("  \n;")

    # Evaluate the cleaned up JSON into a python dict.
    dics = ast.literal_eval(dict_str)
    return(dics)

def YoutubeChatReplayCrawler(video_id):
    youtube_url = "https://www.youtube.com/watch?v="
    headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'}
    next_url_prefix = "https://www.youtube.com/live_chat_replay?continuation="
    target_url = youtube_url + video_id
    dict_str = ''
    next_url = ''
    dics = {}
    comment_data = []
    session = requests.Session()

    html = session.get(target_url, headers=headers)
    soup = BeautifulSoup(html.text, 'html.parser')
    for iframe in soup.find_all("iframe"):
        if("live_chat_replay" in iframe["src"]):
            next_url = iframe["src"]
            print('Found first URL in iframe[src]')
            break
    if next_url == '':
        for script in soup.find_all('script'):
            script_text = str(script)
            if 'ytInitialData' in script_text:
                if 'liveChatRenderer' in script_text:
                    dict_str = ''.join(script_text.split(" = ")[1:]).split('\n')[0]
                    dics = dict_str_to_dic(dict_str)
                    continue_url = dics["contents"]["twoColumnWatchNextResults"]["conversationBar"]["liveChatRenderer"]["continuations"][0]["reloadContinuationData"]["continuation"]
                    next_url = next_url_prefix + continue_url
                    print('Found first URL in liveChatRenderer')
                    break
    if next_url == '':
        # 2つの方法を試して見つからなかったら諦める
        print("Cannot find continuation url")
        return(comment_data) # return empty list

    while(1):
        try:
            dics = {}
            dict_str = ''
            html = session.get(next_url, headers=headers)
            soup = BeautifulSoup(html.text, 'lxml')
            for script in soup.find_all('script'):
                script_text = str(script)
                if 'ytInitialData' in script_text:
                    dict_str = ''.join(script_text.split(" = ")[1:])
                    dics = dict_str_to_dic(dict_str)
                    break

            continue_url = dics["continuationContents"]["liveChatContinuation"]["continuations"][0]["liveChatReplayContinuationData"]["continuation"]
            next_url = next_url_prefix + continue_url

            # Extract the data for each live chat comment.
            for samp in dics["continuationContents"]["liveChatContinuation"]["actions"][1:]:
                # comment_data.append(str(samp) + "\n")
                comment_data.append(str(samp))

        # next_urlが入手できなくなったら終わり
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
            error = str(e)
            if 'liveChatReplayContinuationData' in error:
                print('Hit last live chat segment, finishing job.')
            else:
                print("KeyError")
                print(e)
            break
        except SyntaxError as e:
            print("SyntaxError")
            print(e)
            break
        except KeyboardInterrupt:
            break
        except Exception:
            print("Unexpected error:" + str(sys.exc_info()[0]))

    print("Comment data saved")
    return(comment_data)
