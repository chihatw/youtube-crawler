#!/bin/zsh
# 仮想環境を有効化
today=$(date +"%Y%m%d")
cd /Users/chiha/projects-active/youtube
source venv/bin/activate

# get_recent_videos.py を実行し、エラーは日付付きファイルに記録
errfile="get_recent_videos_error_${today}.txt"
python scripts/get_recent_videos.py 2> "$errfile"

# エラーがなければ batch_summarize.py を実行
if [ ! -s "$errfile" ]; then
    rm "$errfile"
    python scripts/batch_summarize.py
fi
