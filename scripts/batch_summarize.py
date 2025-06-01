from utils import ensure_virtualenv
ensure_virtualenv()
import os
from datetime import datetime
from summarize_youtube_url import summarize_and_save_youtube_url

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECENT_VIDEOS_PATH = os.path.abspath(os.path.join(BASE_DIR, 'assets/recent_videos.txt'))
SUMMARIZED_URLS_PATH = os.path.abspath(os.path.join(BASE_DIR, 'assets/summarized_urls.txt'))


def read_urls_with_dates(filepath):
    """
    recent_videos.txt の各行が "url, published_at, ..." 形式の場合、(url, date) のリストで返す。
    日付がパースできなければ None。
    """
    urls = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('//'):
                continue
            parts = [p.strip() for p in line.split(',')]
            url = parts[0]
            date = None
            if len(parts) > 1:
                try:
                    date = datetime.fromisoformat(parts[1].replace('Z', '+00:00'))
                except Exception:
                    date = None
            urls.append((url, date))
    return urls

def read_urls(filepath):
    """
    summarized_urls.txt からURLのみのリストを返す。
    1行に複数URLが連結されている場合も分割して取得する。
    """
    urls = set()
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                # カンマ・スペース・改行で分割
                for url in line.replace(',', ' ').split():
                    url = url.strip()
                    if url:
                        urls.add(url)
    return urls

def write_summary():
    # 1. 登録チャンネル名リスト
    channel_ids_path = os.path.abspath(os.path.join(BASE_DIR, 'assets/subscribed_channel_ids.txt'))
    channel_names_path = os.path.abspath(os.path.join(BASE_DIR, 'assets/channel_names.txt'))
    id2name = {}
    if os.path.exists(channel_names_path):
        with open(channel_names_path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) == 2:
                    id2name[parts[0]] = parts[1]
    channel_ids = []
    if os.path.exists(channel_ids_path):
        with open(channel_ids_path, 'r', encoding='utf-8') as f:
            channel_ids = [line.strip() for line in f if line.strip()]
    channel_names = [id2name.get(cid, cid) for cid in channel_ids]

    # 2. 最新動画取得基準日 published_after
    published_after_path = os.path.abspath(os.path.join(BASE_DIR, 'assets/temp_published_after.txt'))
    published_after = None
    if os.path.exists(published_after_path):
        with open(published_after_path, 'r', encoding='utf-8') as f:
            published_after = f.read().strip()
        os.remove(published_after_path)
    # fallback: recent_videos.txt の最新 published_at
    if not published_after:
        recent_videos_path = os.path.abspath(os.path.join(BASE_DIR, 'assets/recent_videos.txt'))
        latest_dt = None
        if os.path.exists(recent_videos_path):
            with open(recent_videos_path, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) > 1:
                        try:
                            dt = parts[1]
                            if (not latest_dt) or (dt > latest_dt):
                                latest_dt = dt
                        except Exception:
                            pass
        if latest_dt:
            published_after = latest_dt
    # フォーマット変換
    published_after_str = published_after
    if published_after:
        try:
            from datetime import datetime, timezone, timedelta
            import re
            # 2025-05-31T17:51:26Z or 2025-05-31T17:51:26+00:00
            dt = None
            if published_after.endswith('Z'):
                dt = datetime.strptime(published_after, '%Y-%m-%dT%H:%M:%SZ')
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                # 例: 2025-05-31T17:51:26+00:00
                dt = datetime.fromisoformat(re.sub(r'Z$', '+00:00', published_after))
            jst = dt.astimezone(timezone(timedelta(hours=9)))
            published_after_str = jst.strftime('%Y年%-m月%-d日 %H:%M:%S（日本標準時）')
        except Exception:
            published_after_str = published_after

    # 3. 作成した要約mdリスト（tempファイルから取得）
    created_mds_path = os.path.abspath(os.path.join(BASE_DIR, 'summarized/created_mds.txt'))
    newly_created_mds = []
    if os.path.exists(created_mds_path):
        with open(created_mds_path, 'r', encoding='utf-8') as f:
            newly_created_mds = [line.strip() for line in f if line.strip()]
        os.remove(created_mds_path)
    # 重複除去＋ソート
    newly_created_mds = sorted(set(newly_created_mds))

    # 4. クォータ消費量（usage_logsの先頭行）
    usage_log_path = os.path.abspath(os.path.join(BASE_DIR, 'usage_logs/youtube_quota_usage_log.txt'))
    quota_line = ''
    if os.path.exists(usage_log_path):
        with open(usage_log_path, 'r', encoding='utf-8') as f:
            quota_line = f.readline().strip()
    # daily_total, daily_total_quota
    daily_total = ''
    daily_total_quota = ''
    if quota_line:
        for part in quota_line.split(','):
            if 'daily_total_quota' in part:
                daily_total_quota = part.split(':')[-1].strip()
            if 'daily_total' in part and 'quota' not in part:
                daily_total = part.split(':')[-1].strip()

    # Geminiクォータ消費量
    gemini_log_path = os.path.abspath(os.path.join(BASE_DIR, 'usage_logs/gemini_quota_usage_log.txt'))
    gemini_daily_total = ''
    if os.path.exists(gemini_log_path):
        with open(gemini_log_path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            for part in first_line.split(','):
                if 'daily_total:' in part:
                    gemini_daily_total = part.split(':')[-1].strip()

    # summary.md 出力
    summarized_dir = os.path.abspath(os.path.join(BASE_DIR, 'summarized'))
    summary_path = os.path.abspath(os.path.join(summarized_dir, 'summary.md'))
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write('# batch_summarize.py 実行サマリー\n\n')
        f.write('## 登録チャンネル\n')
        for name in channel_names:
            f.write(f'- {name}\n')
        f.write('\n')
        f.write('## 最新動画取得基準日 (published_after)\n')
        f.write(f'- {published_after_str if published_after_str else "(不明)"}\n\n')
        f.write('## 作成した要約mdファイル一覧\n')
        for md in newly_created_mds:
            f.write(f'- {md}\n')
        f.write('\n')
        f.write('## クォータ消費量\n')
        f.write(f'- daily_total_quota: {daily_total_quota}\n')
        f.write(f'- gemini_daily_total: {gemini_daily_total}\n')

def main():
    summarized_dir = os.path.abspath(os.path.join(BASE_DIR, 'summarized'))
    archive_dir = os.path.join(summarized_dir, 'archive')
    favorites_dir = os.path.join(summarized_dir, 'favorites')
    def get_all_md_files():
        files = set()
        for root, dirs, filenames in os.walk(summarized_dir):
            for fn in filenames:
                if fn.endswith('.md'):
                    files.add(fn)
        return files
    before_files = get_all_md_files()
    # 要約処理
    while True:
        # recent_videos.txt から (url, date) のリスト取得
        recent_urls = read_urls_with_dates(RECENT_VIDEOS_PATH)
        # summarized_urls.txt から既に要約済みのURL取得
        summarized_urls = read_urls(SUMMARIZED_URLS_PATH)
        # 未要約のURLのみ抽出
        unsummarized = [(url, date) for url, date in recent_urls if url not in summarized_urls]
        # 日付の古い順にソート（Noneは最後）
        unsummarized.sort(key=lambda x: (x[1] is None, x[1]))
        if not unsummarized:
            print("未要約のURLはありません。全て処理済みです。")
            break
        # 1件だけ処理
        url, _ = unsummarized[0]
        print(f"要約処理: {url}")
        summarize_and_save_youtube_url(url)
        # summarized_urls.txt に追記
        with open(SUMMARIZED_URLS_PATH, 'a', encoding='utf-8') as f:
            f.write(url + '\n')
        print(f"summarized_urls.txt に追記しました: {url}")
        # summarize_youtube_url_log.txt が空かどうか確認
        log_path = os.path.abspath(os.path.join(BASE_DIR, 'script_logs/summarize_youtube_url_log.txt'))
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as logf:
                if logf.read().strip():
                    print(f"[INFO] {log_path} にエラーログがあるため処理を中断します。")
                    break
    # 全処理後に summary 出力
    write_summary()

if __name__ == '__main__':
    main()
