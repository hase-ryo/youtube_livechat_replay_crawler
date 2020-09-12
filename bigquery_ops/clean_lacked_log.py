from dotenv import load_dotenv
import platform
import json
import sys
import os
from google.cloud import bigquery
from google.oauth2 import service_account
from gcs_wrapper import gcs_wrapper

if platform.system() == 'Darwin':
    # run locally
    load_dotenv('.env')

project_id = os.environ.get("PROJECT_ID")
bucket_name = os.environ.get("GCS_BUCKET_NAME")

def get_bq_client():
    if platform.system() == 'Linux':
        # run at cloud
        client = bigquery.Client()
    elif platform.system() == 'Darwin':
        # run locally
        credentials = service_account.Credentials.from_service_account_file(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"), scopes=["https://www.googleapis.com/auth/cloud-platform"],)
        client = bigquery.Client(credentials=credentials, project=project_id)

    return(client)


def detect_lacked_log():
    with open('./detect_lacked_log.sql') as f:
        query_str = f.read()

    query_str = query_str.format(project_id=project_id)
    bq = get_bq_client()
    result = bq.query(query_str)
    file_paths = []
    channels = {}
    for row in result:
        file_path = row['channel_id'] + '/' + row['video_id'] + '/'
        file_paths.append(file_path)
        videos = channels.get(row['channel_id'], [])
        videos.append(row['video_id'])
        channels[row['channel_id']] = videos

    return(file_paths,channels)

if __name__ == '__main__':
    flg = sys.argv[1]
    file_paths, channels = detect_lacked_log()
    if flg == 'delete':
        for file_path in file_paths:
            gcs_wrapper.search_and_destroy_file(bucket_name, file_path)
    else:
        for channel_id in channels.keys():
            print(channel_id + ':' + ','.join(channels[channel_id]))

