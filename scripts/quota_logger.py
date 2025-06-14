from utils import ensure_virtualenv
ensure_virtualenv()
import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo

def log_quota_usage(
    quota_used: int,
    search_list_count: int,
    videos_list_count: int,
    api_name: str = "youtube",
    caller_program: str = None
):
    """
    <API名>_quota_usage_log.txt に推定クォータ消費量・search.list回数・videos.list回数・記録日時・1日累計推定クォータ消費量・呼び出し元プログラム名を追記する共通関数。
    api_nameでAPI種別を記録し、ログファイル名も自動で決定。
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_file_path = os.path.abspath(os.path.join(base_dir, f"usage_logs/{api_name}_quota_usage_log.txt"))
    now_pst = datetime.now(ZoneInfo("America/Los_Angeles"))
    now_str = now_pst.strftime('%Y-%m-%dT%H:%M:%S%z')
    if len(now_str) > 19:
        now_str = now_str[:19] + now_str[19:22] + ':' + now_str[22:]
    log_date = now_pst.strftime('%Y-%m-%d')
    daily_total = quota_used
    if os.path.exists(log_file_path):
        with open(log_file_path, 'r') as f:
            old_lines = f.readlines()
        for line in old_lines:
            if line.strip() and line[:10] == log_date and f"api: {api_name}" in line:
                m = re.search(r'quota: (\d+)', line)
                if m:
                    daily_total += int(m.group(1))
    else:
        old_lines = []
    # プログラム名が指定されていなければ空文字列
    program_str = f", program: {caller_program}" if caller_program else ""
    log_line = f'{now_str}, api: {api_name}, quota: {quota_used}, search.list: {search_list_count}, videos.list: {videos_list_count}, daily_total_quota: {daily_total}{program_str}\n'
    try:
        with open(log_file_path, 'w') as f:
            f.write(log_line)
            f.writelines(old_lines)
    except Exception as e:
        print(f"[ERROR] Failed to write quota log: {e}")

def log_gemini_quota_usage(prompt_tokens, completion_tokens, total_tokens):
    """
    Gemini APIのトークン使用量をログファイルに追記（先頭に追加、PSTで日時降順）
    """
    from zoneinfo import ZoneInfo
    import datetime
    import os
    log_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'usage_logs/gemini_quota_usage_log.txt'))
    # 現在時刻（PST）
    now = datetime.datetime.now(ZoneInfo("America/Los_Angeles"))
    now_str = now.strftime('%Y-%m-%dT%H:%M:%S%z')
    today_str = now.strftime('%Y-%m-%d')
    # 既存ログ読み込み
    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    else:
        lines = []
    # 同じ日付のtotalを合計
    daily_total = total_tokens
    for line in lines:
        if line.startswith('//'):
            continue
        parts = line.strip().split(',')
        if not parts or len(parts) < 1:
            continue
        # 日付部分を抽出
        date_part = parts[0].split('T')[0]
        if date_part == today_str:
            for p in parts:
                if 'total:' in p and 'daily_total:' not in p:
                    try:
                        daily_total += int(p.split(':')[1].strip())
                    except Exception:
                        pass
    # ログ行作成
    log_line = f"{now_str}, prompt: {prompt_tokens}, completion: {completion_tokens}, total: {total_tokens}, daily_total: {daily_total}\n"
    # 先頭に追記
    lines = [log_line] + [l for l in lines if l.strip()]
    try:
        with open(log_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    except Exception as e:
        print(f"[ERROR] Failed to write gemini quota log: {e}")
