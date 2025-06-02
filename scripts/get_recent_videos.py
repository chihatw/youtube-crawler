from utils import ensure_virtualenv
ensure_virtualenv()

import os
import json
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import re
from zoneinfo import ZoneInfo
from quota_logger import log_quota_usage

# ルートディレクトリを基準にファイルパスを指定
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- ログファイル設定 ---
LOGS_DIR = os.path.abspath(os.path.join(BASE_DIR, 'script_logs'))
os.makedirs(LOGS_DIR, exist_ok=True)
log_date = datetime.now(ZoneInfo('Asia/Tokyo')).strftime('%Y%m%d')
LOG_PATH = os.path.join(LOGS_DIR, f'get_recent_videos_{log_date}.log')

def log(msg):
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')

# .envからAPIキーを取得
load_dotenv(os.path.join(BASE_DIR, '.env'))
API_KEY = os.getenv('API_KEY')

CHANNEL_IDS_FILE = os.path.abspath(os.path.join(BASE_DIR, 'assets/subscribed_channel_ids.txt'))
OUTPUT_FILE = os.path.abspath(os.path.join(BASE_DIR, 'assets/recent_videos.txt'))

# recent_videos.txt から最新日時を取得
recent_videos_path = OUTPUT_FILE
latest_datetime = None
existing_lines = []
existing_urls = set()
if os.path.exists(recent_videos_path):
    with open(recent_videos_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('//'):
                continue
            existing_lines.append(line)
            parts = line.split(',')
            if len(parts) > 1:
                try:
                    dt = datetime.fromisoformat(parts[1].strip().replace('Z', '+00:00'))
                    if (latest_datetime is None) or (dt > latest_datetime):
                        latest_datetime = dt
                except Exception:
                    pass
            if len(parts) > 0:
                existing_urls.add(parts[0].strip())

# 取得基準日時を決定
now_utc = datetime.now(timezone.utc)
if latest_datetime and (now_utc - latest_datetime).total_seconds() <= 86400:
    # 最新日時が1日以内なら、その直後から取得
    published_after = latest_datetime.isoformat().replace('+00:00', 'Z')
else:
    # それ以外は24時間前から取得
    published_after = (now_utc - timedelta(days=1)).isoformat('T').replace('+00:00', 'Z')

# published_after を一時ファイルに保存
TEMP_PUBLISHED_AFTER_PATH = os.path.abspath(os.path.join(BASE_DIR, 'assets/temp_published_after.txt'))
with open(TEMP_PUBLISHED_AFTER_PATH, 'w', encoding='utf-8') as f:
    f.write(published_after + '\n')

def to_jst_str(iso_str):
    try:
        if iso_str.endswith('Z'):
            dt = datetime.strptime(iso_str, '%Y-%m-%dT%H:%M:%SZ')
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = datetime.fromisoformat(re.sub(r'Z$', '+00:00', iso_str))
        jst = dt.astimezone(ZoneInfo('Asia/Tokyo'))
        return jst.strftime('%Y年%m月%d日 %H:%M:%S（日本標準時）')
    except Exception:
        return iso_str
log(f"[INFO] published_after: {published_after}（{to_jst_str(published_after)}）")

with open(CHANNEL_IDS_FILE, 'r') as f:
    channel_ids = [line.strip() for line in f if line.strip() and not line.startswith('//')]

# channel_names.txtを辞書として読み込む
CHANNEL_NAMES_FILE = os.path.abspath(os.path.join(BASE_DIR, 'assets/channel_names.txt'))
channel_id_to_name = {}
with open(CHANNEL_NAMES_FILE, 'r') as f:
    for line in f:
        if line.strip() and not line.startswith('//'):
            parts = line.strip().split('\t')
            if len(parts) == 2:
                channel_id_to_name[parts[0]] = parts[1]

results = []
new_results = []

for channel_id in channel_ids:
    channel_name = channel_id_to_name.get(channel_id, '')
    log(f"[INFO] チャンネル名: {channel_name}")
    url = 'https://www.googleapis.com/youtube/v3/search'
    params = {
        'key': API_KEY,
        'channelId': channel_id,
        'part': 'snippet',
        'order': 'date',
        'publishedAfter': published_after,
        'type': 'video',
        'maxResults': 50
    }
    log(f"[INFO] YouTube APIリクエスト: {url} {params}")
    response = requests.get(url, params=params)
    log(f"[INFO] YouTube APIレスポンス: {response.text[:500]}{'...省略' if len(response.text)>500 else ''}")
    if response.status_code != 200:
        continue
    data = response.json()
    video_titles = []
    count = 0
    for item in data.get('items', []):
        video_id = item['id']['videoId']
        video_url = f'https://www.youtube.com/watch?v={video_id}'
        if video_url in existing_urls:
            continue
        published_at = item['snippet']['publishedAt']
        title = item['snippet']['title']
        video_details_url = 'https://www.googleapis.com/youtube/v3/videos'
        video_details_params = {
            'key': API_KEY,
            'id': video_id,
            'part': 'contentDetails'
        }
        details_response = requests.get(video_details_url, params=video_details_params)
        if details_response.status_code != 200:
            continue
        details_data = details_response.json()
        if not details_data.get('items'):
            continue
        duration = details_data['items'][0]['contentDetails']['duration']
        match = re.match(r'PT(?:(\d+)M)?(?:(\d+)S)?', duration)
        minutes = int(match.group(1)) if match and match.group(1) else 0
        seconds = int(match.group(2)) if match and match.group(2) else 0
        total_seconds = minutes * 60 + seconds
        if total_seconds <= 180:
            continue
        video_titles.append(f"{title}({minutes}:{str(seconds).zfill(2)})")
        count += 1
        new_results.append((published_at, video_url, channel_id, channel_name, title, duration))
    log(f"[INFO] 取得動画数（3分未満除外）: {count}")
    log("[INFO] 取得動画タイトルリスト:")
    for t in video_titles:
        log(f"  - {t}")

# 既存＋新規をまとめて日時降順で並べる
all_results = []
for line in existing_lines:
    parts = [p.strip() for p in line.split(',')]
    if len(parts) >= 6:
        all_results.append((parts[1], parts[0], parts[2], parts[3], parts[4], parts[5]))
all_results.extend(new_results)
all_results.sort(key=lambda x: x[0], reverse=True)

with open(OUTPUT_FILE, 'w') as f:
    for published_at, video_url, channel_id, channel_name, title, duration in all_results:
        f.write(f'{video_url}, {published_at}, {channel_id}, {channel_name}, {title}, {duration}\n')

print(f'新規取得動画数: {len(new_results)}')
print(f'動画情報を {OUTPUT_FILE} に出力しました')

# クォータ消費量の計算
search_list_count = len(channel_ids)  # search.listはチャンネルごとに1回
videos_list_count = sum([1 for r in new_results])  # videos.listは新規動画ごとに1回
quota_used = search_list_count * 100 + videos_list_count * 1

# ログファイルに記録（共通関数利用）
program_name = os.path.splitext(os.path.basename(__file__))[0]
log_quota_usage(quota_used, search_list_count, videos_list_count, api_name="youtube", caller_program=program_name)
