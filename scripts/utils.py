import re

def sanitize_filename(s: str) -> str:
    """
    ファイル名に使えない文字を _ に置換するユーティリティ関数
    """
    return re.sub(r'[\\/:*?"<>|\n\r]', '_', s)
