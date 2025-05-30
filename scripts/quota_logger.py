import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo

def log_quota_usage(
    quota_used: int,
    search_list_count: int,
    videos_list_count: int,
    api_name: str = "youtube"
):
    """
    <API名>_quota_usage_log.txt に推定クォータ消費量・search.list回数・videos.list回数・記録日時・1日累計推定クォータ消費量を追記する共通関数。
    api_nameでAPI種別を記録し、ログファイル名も自動で決定。
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_file_path = os.path.join(base_dir, f"{api_name}_quota_usage_log.txt")
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
    log_line = f'{now_str}, api: {api_name}, quota: {quota_used}, search.list: {search_list_count}, videos.list: {videos_list_count}, daily_total_quota: {daily_total}\n'
    with open(log_file_path, 'w') as f:
        f.write(log_line)
        f.writelines(old_lines)
