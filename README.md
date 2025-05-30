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

API ごとのクォータ消費量やトークン数を記録・管理する共通モジュールです。

- YouTube API 用: `log_quota_usage()` を呼び出すことで `youtube_quota_usage_log.txt` などに記録されます。
- Gemini API 用: `log_gemini_quota_usage()` を呼び出すことで `gemini_quota_usage_log.txt` に送信・受信・合計トークン数と 1 日累計合計トークン数が記録されます。
- どちらのログも PST 基準で日時降順に追記されます。
- Gemini API のログファイルや要約 Markdown ファイル（`summarized/` 配下）は `.gitignore` で管理対象外です。

各スクリプトからこれらの関数を呼び出すことで、API ごとのログファイルに自動的に記録されます。

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

- YouTube API のクォータ消費量のみ `quota_logger.py` を通じて `youtube_quota_usage_log.txt` に記録されます。
- Gemini API のトークン送受信・合計トークン数は `gemini_quota_usage_log.txt` に記録されます（1 日ごとの合計トークン数も記録）。
- Gemini API のログは `.gitignore` で管理対象外です。
- 要約 Markdown ファイル（`summarized/`配下）も `.gitignore` で管理対象外です。

---

## 注意事項

- Google API キーや OAuth 認証情報（`credentials.json`）が必要です。`.env`や`credentials.json`を適切に用意してください。
- 実行結果やログファイル（`*_log.txt`など）は `.gitignore` で Git 管理対象外になっています。
- 各スクリプトの出力ファイルは上書きされます。必要に応じてバックアップを取ってください。

---
