from utils import ensure_virtualenv
ensure_virtualenv()
import os
from dotenv import load_dotenv
load_dotenv()
import googleapiclient.discovery
import googleapiclient.errors
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from zoneinfo import ZoneInfo
import re
from datetime import datetime
from quota_logger import log_quota_usage

# 認証に必要なスコープ
SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

# OAuth2認証フロー
# credentials.jsonはGoogle Cloud Consoleで作成したOAuthクライアントIDのファイル

def get_authenticated_service():
    flow = InstalledAppFlow.from_client_secrets_file(
        "credentials.json", SCOPES)
    credentials = flow.run_local_server(port=0)
    return build("youtube", "v3", credentials=credentials)

def get_subscribed_channel_ids(youtube, max_results=50):
    channel_ids = []
    next_page_token = None
    page = 1
    while True:
        request = youtube.subscriptions().list(
            part="snippet",
            mine=True,
            maxResults=max_results,
            pageToken=next_page_token
        )
        response = request.execute()
        items = response.get("items", [])
        for item in items:
            channel_id = item["snippet"]["resourceId"]["channelId"]
            channel_ids.append(channel_id)
        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break
        page += 1
    return channel_ids

if __name__ == "__main__":
    youtube = get_authenticated_service()
    subscriptions_list_count = 0  # subscriptions.list呼び出し回数
    channel_ids = []
    next_page_token = None
    page = 1
    while True:
        print(f"[DEBUG] subscriptions().list request: page={page}, next_page_token={next_page_token}")
        request = youtube.subscriptions().list(
            part="snippet",
            mine=True,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()
        print(f"[DEBUG] API response keys: {list(response.keys())}")
        subscriptions_list_count += 1
        items = response.get("items", [])
        print(f"[DEBUG] items count: {len(items)}")
        for item in items:
            channel_id = item["snippet"]["resourceId"]["channelId"]
            print(f"[DEBUG] Got channel_id: {channel_id}")
            channel_ids.append(channel_id)
        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break
        page += 1
    # 出力ファイル名を絶対パスで指定
    output_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/subscribed_channel_ids.txt"))
    print(f"[DEBUG] Writing {len(channel_ids)} channel_ids to {output_file}")
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            for cid in channel_ids:
                f.write(cid + "\n")
        print(f"登録チャンネルのchannel_idリストを {output_file} に出力しました。")
    except Exception as e:
        print(f"[ERROR] Failed to write to {output_file}: {e}")

    # クォータ消費量の計算とログ
    quota_used = subscriptions_list_count * 5
    search_list_count = 0
    videos_list_count = 0
    # 呼び出し元プログラム名を渡す
    program_name = os.path.splitext(os.path.basename(__file__))[0]
    log_quota_usage(quota_used, search_list_count, videos_list_count, api_name="youtube", caller_program=program_name)
