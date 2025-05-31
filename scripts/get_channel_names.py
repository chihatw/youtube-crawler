from utils import ensure_virtualenv
ensure_virtualenv()

import os
import googleapiclient.discovery
from dotenv import load_dotenv
from quota_logger import log_quota_usage

# .envファイルからAPIキーを取得
load_dotenv()
api_key = os.getenv('API_KEY')

# 入力ファイルと出力ファイルのパス
input_file = '../subscribed_channel_ids.txt'
output_file = '../channel_names.txt'

def get_channel_name(channel_id, api_key):
    youtube = googleapiclient.discovery.build('youtube', 'v3', developerKey=api_key)
    request = youtube.channels().list(
        part='snippet',
        id=channel_id
    )
    response = request.execute()
    # 1回のchannels.list呼び出しごとにカウント
    get_channel_name.api_call_count += 1
    items = response.get('items', [])
    if items:
        return items[0]['snippet']['title']
    else:
        return None
get_channel_name.api_call_count = 0

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

    # クォータ消費量の計算とログ
    quota_used = get_channel_name.api_call_count * 1  # channels.listは1回1unit
    search_list_count = 0
    videos_list_count = 0
    program_name = os.path.splitext(os.path.basename(__file__))[0]
    log_quota_usage(quota_used, search_list_count, videos_list_count, api_name="youtube", caller_program=program_name)

if __name__ == '__main__':
    main()
