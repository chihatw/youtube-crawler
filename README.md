# YouTube クローラースクリプト集

このリポジトリは、YouTube Data API や Gemini API を利用した Python スクリプト群です。  
主にチャンネル情報・動画情報の取得や要約、API クォータ管理を行います。

---

## 仮想環境の利用

依存関係の競合やバージョン違いによるトラブルを避けるため、**仮想環境の利用を推奨**します。

1. 仮想環境を有効化（初回のみ仮想環境を作成してください）

   ```sh
   python3 -m venv venv
   source venv/bin/activate
   ```

2. 必要なパッケージをインストール

   ```sh
   pip install -r requirements.txt
   ```

3. スクリプトを実行

   ```sh
   python3 scripts/xxx.py
   ```

4. 仮想環境を無効化

   ```sh
   deactivate
   ```

---

## スクリプト一覧

### quota_logger.py

API ごとのクォータ消費量を記録・管理する共通モジュールです。  
各スクリプトから `log_quota_usage()` を呼び出すことで、  
`youtube_quota_usage_log.txt` など API ごとのログファイルに

- 記録日時（PST 基準）
- 推定クォータ消費量
- search.list 回数
- videos.list 回数
- 1 日累計推定クォータ消費量  
  を追記します。

### get_subscribed_channels.py

YouTube API（subscriptions.list）を使用して、ユーザーが購読しているチャンネルの channel_id リストを取得し、  
`subscribed_channel_ids.txt` に出力します。  
API クォータ消費量は `quota_logger.py` を通じて `youtube_quota_usage_log.txt` に記録されます。

#### 使い方

```sh
python3 scripts/get_subscribed_channels.py
```

OAuth 2.0 認証のため、ブラウザが開きます。認証後、`subscribed_channel_ids.txt` にチャンネル ID リストが保存されます。

---

### get_channel_names.py

`subscribed_channel_ids.txt` の各チャンネル ID について、YouTube API（channels.list）でチャンネル名を取得し、  
`channel_names.txt` に ID と名前の対応表を出力します。  
API クォータ消費量は `quota_logger.py` を通じて `youtube_quota_usage_log.txt` に記録されます。

---

### get_recent_videos.py

`subscribed_channel_ids.txt` の各チャンネルについて、YouTube API（search.list, videos.list）で  
最近の動画情報を取得し、`recent_videos.txt` に出力します。  
API クォータ消費量は `quota_logger.py` を通じて `youtube_quota_usage_log.txt` に記録されます。

---

### summarize_youtube_url.py

YouTube 動画の説明文を YouTube Data API で取得し、Gemini API で要約します。  
YouTube API のクォータ消費量のみ `quota_logger.py` を通じて `youtube_quota_usage_log.txt` に記録されます。

---

## 注意事項

- Google API キーや OAuth 認証情報（`credentials.json`）が必要です。`.env`や`credentials.json`を適切に用意してください。
- 実行結果やログファイル（`*_log.txt`など）は `.gitignore` で Git 管理対象外になっています。
- 各スクリプトの出力ファイルは上書きされます。必要に応じてバックアップを取ってください。

---
