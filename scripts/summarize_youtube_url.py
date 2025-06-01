from utils import ensure_virtualenv
ensure_virtualenv()

import os
from dotenv import load_dotenv
import google.generativeai as genai
import requests
from quota_logger import log_quota_usage, log_gemini_quota_usage
from utils import sanitize_filename, ensure_virtualenv

# --- 追加: ログファイルのパス ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_PATH = os.path.abspath(os.path.join(BASE_DIR, 'script_logs/summarize_youtube_url_log.txt'))

# --- 追加: ログファイルが空でなければ停止 ---
if os.path.exists(LOG_PATH):
    with open(LOG_PATH, 'r', encoding='utf-8') as logf:
        if logf.read().strip():
            print(f"[INFO] {LOG_PATH} にエラーログがあるため処理を中断します。")
            exit(0)

# Gemini APIキーのロード
dotenv_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

def get_youtube_description(video_id: str, api_key: str) -> str:
    """
    YouTube Data APIで動画の説明文(description)を取得
    """
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        'id': video_id,
        'part': 'snippet',
        'key': api_key
    }
    resp = requests.get(url, params=params)
    # API呼び出し回数をカウント
    get_youtube_description.api_call_count += 1
    if resp.status_code != 200:
        print(f"[ERROR] YouTube API error: {resp.text}")
        return {}, ""
    items = resp.json().get('items', [])
    if not items:
        return {}, ""
    snippet = items[0]['snippet']
    meta = {
        'title': snippet.get('title', ''),
        'channelTitle': snippet.get('channelTitle', ''),
        'publishedAt': snippet.get('publishedAt', ''),
        'thumbnail': snippet.get('thumbnails', {}).get('high', {}).get('url', '')
    }
    description = snippet.get('description', '')
    return meta, description
get_youtube_description.api_call_count = 0

def summarize_youtube_url(meta: dict, description: str, youtube_url: str) -> str:
    """
    YouTube動画のメタ情報と説明文をもとにGemini APIで要約を取得する
    """
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')
    prompt = f"""
    以下のYouTube動画の情報と説明文をもとに、日本語で要約してください。
    チャンネル名: {meta.get('channelTitle','')}
    動画タイトル: {meta.get('title','')}
    公開日時: {meta.get('publishedAt','')}
    サムネイルURL: {meta.get('thumbnail','')}
    動画URL: {youtube_url}
    説明文: {description}
    """
    response = model.generate_content(prompt)
    summarize_youtube_url.api_call_count += 1
    # トークン数取得
    prompt_tokens = response.usage_metadata.prompt_token_count
    completion_tokens = response.usage_metadata.candidates_token_count
    total_tokens = response.usage_metadata.total_token_count
    # Geminiトークン使用量をログ
    log_gemini_quota_usage(prompt_tokens, completion_tokens, total_tokens)
    return response.text.strip()
summarize_youtube_url.api_call_count = 0

def summarize_and_save_youtube_url(youtube_url: str) -> None:
    """
    指定したYouTube URLの要約を生成し、ファイルに保存する
    """
    try:
        video_id = youtube_url.split('v=')[-1]
        YT_API_KEY = os.getenv('API_KEY')
        meta, description = get_youtube_description(video_id, YT_API_KEY)
        if not description:
            print("[ERROR] 動画の説明文が取得できませんでした。")
            summary = "(説明文が取得できませんでした)"
        else:
            summary = summarize_youtube_url(meta, description, youtube_url)
        out_dir = os.path.abspath(os.path.join(BASE_DIR, 'summarized'))
        os.makedirs(out_dir, exist_ok=True)
        channel = sanitize_filename(meta.get('channelTitle', 'unknown'))
        title = sanitize_filename(meta.get('title', 'unknown'))
        out_path = os.path.abspath(os.path.join(out_dir, f"{channel}_{title}.md"))
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(f"# [{meta.get('title','')}]({youtube_url})\n\n")
            f.write(f"**チャンネル名:** {meta.get('channelTitle','')}\n\n")
            f.write(f"**公開日時:** {meta.get('publishedAt','')}\n\n")
            f.write(f"**サムネイル:** ![]({meta.get('thumbnail','')})\n\n")
            f.write(f"{summary}\n")
        print(f"要約を {out_path} に保存しました")
        # 追加: 作成したmdファイル名を temp ファイルに追記
        created_mds_path = os.path.abspath(os.path.join(BASE_DIR, 'summarized/created_mds.txt'))
        with open(created_mds_path, 'a', encoding='utf-8') as f:
            f.write(f"{channel}_{title}.md\n")
        quota_used = get_youtube_description.api_call_count * 1
        search_list_count = 0
        videos_list_count = get_youtube_description.api_call_count
        program_name = os.path.splitext(os.path.basename(__file__))[0]
        log_quota_usage(quota_used, search_list_count, videos_list_count, api_name="youtube", caller_program=program_name)
    except Exception as e:
        with open(LOG_PATH, 'a', encoding='utf-8') as logf:
            import traceback
            logf.write(f"[ERROR] {str(e)}\n")
            logf.write(traceback.format_exc())
        print(f"[ERROR] エラー内容を {LOG_PATH} に記録しました。")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        url = sys.argv[1]
        summarize_and_save_youtube_url(url)
    else:
        print("使い方: python summarize_youtube_url.py <YouTubeのURL>")
