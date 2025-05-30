import os
import googleapiclient.discovery
import googleapiclient.errors

import re
from dotenv import load_dotenv
# .envファイルから環境変数を読み込む
load_dotenv()
api_key=os.getenv('API_KEY')

# デスクトップのパスを取得
desktop_path = os.path.expanduser('~/Desktop')

# 保存するファイル名とパスを指定
file_path = os.path.join(desktop_path, 'output.txt')

def get_latest_videos(channel_id, api_key, max_results=5):
    """
    指定されたチャンネルの最新の動画タイトルを取得します。

    Args:
        channel_id (str): YouTubeチャンネルのID。
        api_key (str): Google Cloud Platform で取得した API キー。
        max_results (int): 取得する動画の最大数。

    Returns:
        list: 最新の動画タイトルのリスト。エラーが発生した場合は None を返します。
    """
    try:
        youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)

        request = youtube.search().list(
            part="snippet",
            channelId=channel_id,
            order="date",
            type="video",
            maxResults=max_results
        )
        response = request.execute()

        video_titles = [item["snippet"]["title"] for item in response.get("items", [])]
        return video_titles

    except googleapiclient.errors.HttpError as e:
        print(f"An HTTP error {e.resp.status} occurred:\n{e.content}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

if __name__ == "__main__":
    channel_id = "UCmMnzrvnsSnv-0u9M1Rxiqw"  
    latest_titles = get_latest_videos(channel_id, api_key)

    with open(file_path, 'w' ,encoding='utf-8') as file:
        if latest_titles:
            file.write(f"{channel_id} の最新動画:\n")
            for title in latest_titles:
                match = re.match(r"^(.*?)【", title)
                if match and match.group(1):
                        result = match.group(1)
                        file.write(f"{result}\n")    
                else:
                        file.write(f"{title}\n")    
        else:
            file.write("最新の動画タイトルを取得できませんでした。")