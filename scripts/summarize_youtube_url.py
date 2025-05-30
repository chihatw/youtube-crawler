import os
from dotenv import load_dotenv
import google.generativeai as genai
import requests
from quota_logger import log_quota_usage, log_gemini_quota_usage

# Gemini APIキーのロード
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
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
    Gemini APIにYouTube URLを直接渡して要約を取得する
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

if __name__ == "__main__":
    # テスト用URL
    youtube_url = "https://www.youtube.com/watch?v=b1TeeIG6Uaw"
    video_id = youtube_url.split('v=')[-1]
    # YouTube APIキー
    YT_API_KEY = os.getenv('API_KEY')
    meta, description = get_youtube_description(video_id, YT_API_KEY)
    if not description:
        print("[ERROR] 動画の説明文が取得できませんでした。")
        summary = "(説明文が取得できませんでした)"
    else:
        summary = summarize_youtube_url(meta, description, youtube_url)
    # 出力先ディレクトリ
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'summarized')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{video_id}.md")
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(f"# 要約: {youtube_url}\n\n")
        f.write(f"**チャンネル名:** {meta.get('channelTitle','')}\n\n")
        f.write(f"**動画タイトル:** {meta.get('title','')}\n\n")
        f.write(f"**公開日時:** {meta.get('publishedAt','')}\n\n")
        f.write(f"**サムネイル:** ![]({meta.get('thumbnail','')})\n\n")
        f.write(f"{summary}\n")
    print(f"要約を {out_path} に保存しました")
    # YouTube APIクォータログ
    quota_used = get_youtube_description.api_call_count * 1  # videos.listは1回1unit
    search_list_count = 0
    videos_list_count = get_youtube_description.api_call_count  # videos.listのみカウント
    log_quota_usage(quota_used, search_list_count, videos_list_count, api_name="youtube")
