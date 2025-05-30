# youtube_crawler.py

`youtube_crawler.py` は Automator で使用するための Python スクリプトです。  
「取得片名.app」で利用されています。

## 使い方

1. 仮想環境を有効化（初回のみ仮想環境を作成してください）

   ```shell
   python3 -m venv venv
   source venv/bin/activate
   ```

2. 必要なパッケージをインストール

   ```shell
   pip install google-api-python-client
   ```

3. スクリプトを実行

   ```shell
   python3 youtube_crawler.py
   ```

4. 仮想環境を無効化

   ```shell
   deactivate
   ```

## 注意事項

- 依存関係の競合やバージョン違いによるトラブルを避けるため、仮想環境の利用を推奨します。
- Google API キーが必要です。`youtube_crawler.py` 内の `api_key` をご自身のものに書き換えてください。
- 実行結果はデスクトップの `output.txt` に保存されます。

---

# get_subscribed_channels.py

`get_subscribed_channels.py` は、YouTube API を使用してユーザーが購読しているチャンネルの channel_id リストを取得し、`subscribed_channel_ids.txt` というテキストファイルに出力するスクリプトです。

## 使い方

```shell
python3 get_subscribed_channels.py
```

OAuth 2.0 認証のため、ブラウザが開きます。認証後、`subscribed_channel_ids.txt` にチャンネル ID リストが保存されます。

OAuth 2.0 認証には、あらかじめ [Google Cloud Console](https://console.cloud.google.com) でテストユーザーの Email アドレスを設定しておく必要があります。

## 注意事項

- 初回実行時は `credentials.json`（Google Cloud Console で作成した OAuth クライアント ID ファイル）が必要です。
- 仮想環境の利用を推奨します。
- 必要なパッケージは下記コマンドでインストールしてください。

  ```shell
  pip install google-api-python-client google-auth-oauthlib
  ```

---

# get_recent_videos.py

`get_recent_videos.py` は、登録チャンネル（`subscribed_channel_ids.txt`）から YouTube 動画の最新 URL リストを取得し、`recent_videos.txt` に追記・管理するスクリプトです。

- `recent_videos.txt` から最新日時を取得し、その日時以降の動画のみ取得します。
- ファイルが空の場合は過去 3 日以内の動画を取得します。
- 取得した動画は重複を避けて追記し、日時降順で並べます。
- ショート動画（180 秒以下）は除外されます。

## 使い方

```shell
python3 scripts/get_recent_videos.py
```

---

# summarize_youtube_url.py

`summarize_youtube_url.py` は、YouTube 動画の説明文やメタ情報（チャンネル名・タイトル・公開日時・サムネイル）を YouTube Data API で取得し、その内容を Gemini API で要約して `summarized/` フォルダにマークダウン形式で保存するスクリプトです。

- 動画 ID から説明文・チャンネル名・タイトル・公開日時・サムネイル URL を取得
- それらの情報を Gemini API（例: gemini-2.0-flash）に渡して要約
- 結果を `summarized/動画ID.md` に保存

## 使い方

```shell
pip install google-generativeai python-dotenv requests
python3 scripts/summarize_youtube_url.py
```

`.env` に `API_KEY`（YouTube Data API キー）と `GEMINI_API_KEY`（Gemini API キー）が必要です。

---
