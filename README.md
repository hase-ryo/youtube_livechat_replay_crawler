# Youtube Livechat Replay Crawler

This script's purpose is to get live chat comments from Youtube.
For get chat log from Youtube video archives, use HTTP crawling.

This script depend on Google Cloud Platform.
For example, get/put file from/to Cloud Storage, or publish/subscribe message data from Cloud Pub/Sub.
If you run this script only locally, customize main function and make sure to call only the functions you need.

The script is split into several parts.
At this document, introduce overview of each scripts.

## Scripts overview

### channel_video_list

Get a list of publicly available videos from the Youtube Data API.
The argument is a Channel ID.
Place the retrieved list in Google Cloud Storage.

### untouched_video_checker

Identify videos that have not been stored chat log.
Compare the GCS file list with the list of publicly available videos.
Send the ID of the identified video to Google Cloud Pub/Sub.

### initial_livechat_check

Get the HTTP source from the Youtube video page.
The arguments are channel id and video id.
Determines if a chat log exists.
Searches for URLs to be retrieved on a continuous basis.
If it exists, send it to the Pub/Sub.

### continuation_livechat_crawler

Get the chat log continuously.
The argument is the URL where the first chat log is stored.
Get 800 pages of chat logs.
If there is still a continuation, send the following URL to the Pub/Sub.
Finish when the rest is gone.

### bigquery_ops

Loads the data stored in GCS to BigQuery.
It starts manually.
If the total number of chat logs is low compared to the video time, mark it as uncollected video.
Remove uncollected video.

### gcs_wrapper (external submodule)

External sub-modules for performing various operations on GCS.
Read GCS files into a dict type or list type, and vice versa.

# If you run it locally

Run `locally_run.py` in the `continuation_livechat_crawler` with `video_id`.

```
python continuation_livechat_crawler/locally_run.py ABCDEFG
```

`video_id` is taken from youtube URL, `https://www.youtube.com/watch?v=video_id`

# Original Idea & Special Thanks

The original idea of this script is by Mr.watagasi_'s this blog

http://watagassy.hatenablog.com/entry/2018/10/08/132939

And, two contributer forked and made improvement.

Mr.kkorona
https://github.com/kkorona/youtube_chat_crawler

Mr.geerlingguy
https://github.com/geerlingguy/youtube_chat_crawler

Eventually, I also referred to Mr.nolannlum's chatdump.py script.

https://gist.github.com/nolanlum/dd160e6ae752093aa5d98998bd0728a6

I have a deep respect for these predecessors.
THANKS FOR THE GREAT DEVELOPMENT.
I hope you will improve further.

# License

MIT

# Watch Out!!!

Youtube is monetizing by showing ads to humans.
In other words, it's not desirable for them to have machines watching Youtube. Because machines don't respond to ads.
So you... when you run this program, make sure it doesn't touch the wrath of Youtube.
If you are going to run this program in a corporation, I recommend you to go to Youtube's terms and conditions before you do anything fancy.
If you're a private person, do it within the scope of Youtube's generosity.
