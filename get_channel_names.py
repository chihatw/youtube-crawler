import os
import googleapiclient.discovery
from dotenv import load_dotenv

# .envファイルからAPIキーを取得
load_dotenv()
api_key = os.getenv('API_KEY')

# 入力ファイルと出力ファイルのパス
input_file = 'subscribed_channel_ids.txt'
output_file = 'channel_names.txt'

def get_channel_name(channel_id, api_key):
    youtube = googleapiclient.discovery.build('youtube', 'v3', developerKey=api_key)
    request = youtube.channels().list(
        part='snippet',
        id=channel_id
    )
    response = request.execute()
    items = response.get('items', [])
    if items:
        return items[0]['snippet']['title']
    else:
        return None

def main():
    with open(input_file, 'r', encoding='utf-8') as f:
        channel_ids = [line.strip() for line in f if line.strip()]

    with open(output_file, 'w', encoding='utf-8') as f:
        for cid in channel_ids:
            name = get_channel_name(cid, api_key)
            if name:
                f.write(f'{cid}\t{name}\n')
            else:
                f.write(f'{cid}\tチャンネル名取得失敗\n')
    print(f'チャンネル名リストを {output_file} に出力しました。')

if __name__ == '__main__':
    main()
