#!/usr/bin/env python3

import ast
import json

def chatReplayConverter(comment_data, video_id):

    count = 1
    result = []
    for line in comment_data:
        if 'liveChatTickerPaidMessageItemRenderer' in line:
            continue
        if 'liveChatTextMessageRenderer' not in line and 'liveChatPaidMessageRenderer' not in line:
            continue
        ql = line
        frac = {}
        frac['video_id'] = video_id
        frac['Chat_No'] = ("%05d" % count)
        info = ast.literal_eval(ql)

        # Case Normal Chat
        if 'liveChatTextMessageRenderer' in line:
            info = info['replayChatItemAction']['actions'][0]['addChatItemAction']['item']['liveChatTextMessageRenderer']
            content = ""
            if 'simpleText' in info['message']:
                content = info['message']['simpleText']
            elif 'runs' in info['message']:
                for fragment in info['message']['runs']:
                    if 'text' in fragment:
                        content += fragment['text']
                    if 'emoji' in fragment:
                        content += fragment['emoji']['shortcuts'][0]
            else:
                print("no text")
                continue

            frac['user'] = info['authorName']['simpleText']
            frac['timestampUsec'] = info['timestampUsec']
            if 'authorBadges' in info:
                frac['authorbadge'] = info['authorBadges'][0]['liveChatAuthorBadgeRenderer']['tooltip']
            else:
                frac['authorbadge'] = ""

            frac['time'] = info['timestampText']['simpleText']
            frac['purchaseAmount'] = ""
            frac['text'] = content
            frac['type'] = "NORMALCHAT"

        # Case Super Chat
        if 'liveChatPaidMessageRenderer' in line:
            info = info['replayChatItemAction']['actions'][0]['addChatItemAction']['item']['liveChatPaidMessageRenderer']
            content = ""
            if 'message' in info:
                if 'simpleText' in info['message']:
                    content = info['message']['simpleText']
                elif 'runs' in info['message']:
                    for fragment in info['message']['runs']:
                        if 'text' in fragment:
                            content += fragment['text']
                        if 'emoji' in fragment:
                            content += fragment['emoji']['shortcuts'][0]
                else:
                    print("no text")
                    continue

            frac['user'] = info['authorName']['simpleText']
            frac['timestampUsec'] = info['timestampUsec']
            if 'authorBadges' in info:
                frac['authorbadge'] = info['authorBadges'][0]['liveChatAuthorBadgeRenderer']['tooltip']
            else:
                frac['authorbadge'] = ""

            frac['time'] = info['timestampText']['simpleText']
            frac['purchaseAmount'] = info['purchaseAmountText']['simpleText']
            frac['text'] = content
            frac['type'] = "SUPERCHAT"

        result.append(json.dumps(frac, ensure_ascii=False))
        count += 1

    return(result)



