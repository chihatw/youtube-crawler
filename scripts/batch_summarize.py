import os
from datetime import datetime
from summarize_youtube_url import summarize_and_save_youtube_url

RECENT_VIDEOS_PATH = os.path.join(os.path.dirname(__file__), '../recent_videos.txt')
SUMMARIZED_URLS_PATH = os.path.join(os.path.dirname(__file__), '../summarized_urls.txt')


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

def main():
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
        log_path = os.path.join(os.path.dirname(__file__), '../summarize_youtube_url_log.txt')
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as logf:
                if logf.read().strip():
                    print(f"[INFO] {log_path} にエラーログがあるため処理を中断します。")
                    break

if __name__ == '__main__':
    main()
