import re
import sys
import os

def sanitize_filename(s: str) -> str:
    """
    ファイル名に使えない文字を _ に置換するユーティリティ関数
    """
    return re.sub(r'[\\/:*?"<>|\n\r]', '_', s)

def ensure_virtualenv():
    """
    仮想環境で実行されているかを判定し、そうでなければ警告を出して終了する
    """
    if sys.prefix == sys.base_prefix and 'VIRTUAL_ENV' not in os.environ:
        print("警告: 仮想環境外で実行されています。仮想環境を有効化してから再実行してください。")
        exit(1)
