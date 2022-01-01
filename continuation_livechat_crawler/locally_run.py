import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from continuation_livechat_crawler.main import get_ytInitialData, get_continuation, convert_chatreplay, get_chat_replay_from_continuation, RestrictedFromYoutube
from initial_livechat_check.main import get_initial_continuation, check_livechat_replay_disable, ContinuationURLNotFound, LiveChatReplayDisabled, RestrictedFromYoutube
import json

if __name__ == '__main__':
    video_id = sys.argv[1]
    target_url = "https://www.youtube.com/watch?v=" + video_id

    continuation = get_initial_continuation(target_url)
    comment_data, continuation = get_chat_replay_from_continuation(video_id, continuation, 3000, True)

    dmplist = []
    for line in comment_data:
        dmplist.append(json.dumps(line, ensure_ascii=False))

    output_file = './chatlog_replay_' + video_id + '.json'
    with open(output_file, mode='w', encoding='utf-8') as f:
        f.write('\n'.join(dmplist))

    print('DONE!')

