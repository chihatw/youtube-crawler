import os
import googleapiclient.discovery
import googleapiclient.errors
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

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
    while True:
        request = youtube.subscriptions().list(
            part="snippet",
            mine=True,
            maxResults=max_results,
            pageToken=next_page_token
        )
        response = request.execute()
        for item in response.get("items", []):
            channel_id = item["snippet"]["resourceId"]["channelId"]
            channel_ids.append(channel_id)
        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break
    return channel_ids

if __name__ == "__main__":
    youtube = get_authenticated_service()
    channel_ids = get_subscribed_channel_ids(youtube)
    output_file = "subscribed_channel_ids.txt"  # 出力ファイル名
    with open(output_file, "w", encoding="utf-8") as f:
        for cid in channel_ids:
            f.write(cid + "\n")
    print(f"登録チャンネルのchannel_idリストを {output_file} に出力しました。")
