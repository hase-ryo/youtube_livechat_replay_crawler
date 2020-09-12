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

def load_videos():
    client = get_bq_client()
    job_config = bigquery.LoadJobConfig(
        schema = [
            bigquery.SchemaField("channel_id", "STRING"),
            bigquery.SchemaField("published_at", "TIMESTAMP"),
            bigquery.SchemaField("title", "STRING"),
            bigquery.SchemaField("video_id", "STRING"),
            bigquery.SchemaField("duration", "STRING"),
        ],
        #clustering_fields
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
    )

    uri = 'gs://youtube-channel-videos-v2/videos_v2/*.json'
    table_id = project_id + '.Vtuber.videos'
    load_job = client.load_table_from_uri(
            uri, table_id, job_config = job_config
        )
    load_job.result()

    dest_table = client.get_table(table_id)
    print("BQ Loaded {} rows".format(dest_table.num_rows))

def load_chatlogs():
    client = get_bq_client()
    job_config = bigquery.LoadJobConfig(
        schema = [
            bigquery.SchemaField("user", "STRING"),
            bigquery.SchemaField("timestampUsec", "NUMERIC"),
            bigquery.SchemaField("time", "STRING"),
            bigquery.SchemaField("authorbadge", "STRING"),
            bigquery.SchemaField("text", "STRING"),
            bigquery.SchemaField("purchaseAmount", "STRING"),
            bigquery.SchemaField("type", "STRING"),
            bigquery.SchemaField("video_id", "STRING"),
            bigquery.SchemaField("Chat_No", "STRING"),
        ],
        #clustering_fields
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
    )

    uri = 'gs://youtube-livechat-replay-log-v2/*'
    table_id = project_id + '.livechatlog.chatlog'
    load_job = client.load_table_from_uri(
            uri, table_id, job_config = job_config
        )
    load_job.result()

    dest_table = client.get_table(table_id)
    print("BQ Loaded {} rows".format(dest_table.num_rows))


if __name__ == '__main__':
    load_videos()
    load_chatlogs()
