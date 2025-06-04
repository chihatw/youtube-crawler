# YouTube クローラースクリプト集

このリポジトリは、YouTube Data API や Gemini API を利用した Python スクリプト群です。  
主にチャンネル情報・動画情報の取得や要約、API クォータ管理を行います。

---

## 仮想環境の利用

依存関係の競合やバージョン違いによるトラブルを避けるため、**仮想環境の利用を推奨**します。

1. 仮想環境を作成（初回のみ）

   ```sh
   python3 -m venv venv
   ```

2. 仮想環境を有効化（毎回必要）

   ```sh
   source venv/bin/activate
   ```

3. 必要なパッケージをインストール

   ```sh
   pip install -r requirements.txt
   ```

4. スクリプトを実行

   ```sh
   python3 scripts/xxx.py
   ```

5. 仮想環境を無効化

   ```sh
   deactivate
   ```

---

## 仮想環境チェック機能について

本リポジトリの `scripts/` 配下の全ての Python スクリプトは、仮想環境での実行を前提としています。

- 仮想環境外でスクリプトを実行した場合、
  - 「仮想環境外で実行されています。仮想環境を有効化してから再実行してください。」
    という警告が表示され、スクリプトは即座に終了します。
- 依存パッケージが未インストールでも、仮想環境外なら import エラーより先に警告が表示されます。
- 仮想環境の有効化方法は上記「仮想環境の利用」を参照してください。

---

## スクリプト一覧

### quota_logger.py

API ごとのクォータ消費量やトークン数を記録・管理する共通モジュールです。

- YouTube API 用: `log_quota_usage()` を呼び出すことで `youtube_quota_usage_log.txt` などに記録されます。
  - **2025 年 5 月以降、全スクリプトで「クォータを消費したプログラム名」も自動記録されます（`program: xxx` 列が追加されます）。**
- Gemini API 用: `log_gemini_quota_usage()` を呼び出すことで `gemini_quota_usage_log.txt` に送信・受信・合計トークン数と 1 日累計合計トークン数が記録されます。
  - **2025 年 5 月 30 日以降、Gemini の `daily_total` は「直下の行の daily_total に自身の total を加えた値」として正しく記録されます。**
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

- 取得期間は「recent_videos.txt の最新日時が 1 日以内ならその直後から取得、そうでなければ 24 時間前から取得」です。
- 新規取得動画数が標準出力に表示されます。
  API クォータ消費量は `quota_logger.py` を通じて `youtube_quota_usage_log.txt` に記録されます。

---

### summarize_youtube_url.py（2025/05/31 更新）

- 1 つの YouTube 動画 URL を**コマンドライン引数で受け取り**、要約 Markdown を生成・保存する `summarize_and_save_youtube_url(youtube_url: str)` 関数を提供します。
- 直接実行時は `python3 scripts/summarize_youtube_url.py <YouTubeのURL>` のように URL を指定してください。
- 他のスクリプトからも関数呼び出しで要約処理を利用できます。
- エラー時は `summarize_youtube_url_log.txt` に記録されます。

---

### batch_summarize.py（バッチ要約スクリプト・自動ループ対応）

`recent_videos.txt` から未要約の URL を日付の古い順に自動で 1 件ずつ要約し、`summarized_urls.txt` に記録します。

- 1 件処理ごとに `summarized_urls.txt` へ追記します。
- `summarize_youtube_url_log.txt` が空であれば、次の未処理 URL を自動で処理し続けます。
- エラーが `summarize_youtube_url_log.txt` に記録された時点、または全 URL 処理済みで停止します。
- `recent_videos.txt` の形式は `get_recent_videos.py` の出力仕様（カンマ区切り）に対応しています。
- `summarized_urls.txt` に既に記載された URL はスキップされます。
- **1 行に複数 URL が連結されている場合も自動で分割して重複処理を防ぎます。**
- **作成した要約 md ファイル一覧は、`summarize_youtube_url.py` で一時ファイル（`summarized/created_mds.txt`）に記録し、`batch_summarize.py` でそれを読み取って `summary.md` に出力します。**
- **`published_after` の値は日本標準時で「YYYY 年 M 月 D 日 H:M:S（日本標準時）」の形式で summary.md に記載されます。**
- **クォータ消費量の `daily_total` 行は出力されず、`daily_total_quota` と `gemini_daily_total` のみ記載されます。**
- **2025 年 6 月以降、`summarized_urls.txt` には「URL, 公開日時（日本標準時）」の形式で記録されます。**

#### 使い方

```sh
python3 scripts/batch_summarize.py
```

- 途中でエラーが発生した場合は `summarize_youtube_url_log.txt` を確認してください。
- エラー解消後、再度実行すれば未処理分から再開します。
- **`summarized_urls.txt` は 1 行につき 1URL となるようにしてください。もし 1 行に複数 URL が連結されている場合は手動で修正してください。**

---

## 自動要約スクリプトの定期実行について

### scripts/run_daily_youtube_tasks.sh について

- 仮想環境を有効化し、`get_recent_videos.py` を実行します。
- エラーが発生した場合は `get_recent_videos_error_YYYYMMDD.txt` に記録されます。
- エラーがなければ `batch_summarize.py` を続けて実行します。

### launchd での自動実行設定方法（macOS）

1. **スクリプトの実行権限を付与**

   ```zsh
   chmod +x scripts/run_daily_youtube_tasks.sh
   ```

2. **launchd 用 plist ファイルの配置**

   `com.chiha.youtube.daily.plist` を `~/Library/LaunchAgents/` にコピーします。

   ```zsh
   cp com.chiha.youtube.daily.plist ~/Library/LaunchAgents/
   chmod 644 ~/Library/LaunchAgents/com.chiha.youtube.daily.plist
   ```

3. **plist 内のスクリプトパスが正しいことを確認**

   `ProgramArguments` のパスが `scripts/run_daily_youtube_tasks.sh` になっていることを確認してください。

4. **launchd へ登録**

   ```zsh
   launchctl unload ~/Library/LaunchAgents/com.chiha.youtube.daily.plist 2>/dev/null
   launchctl load ~/Library/LaunchAgents/com.chiha.youtube.daily.plist
   ```

5. **動作確認**

   スクリプトを手動実行して動作を確認できます。

   ```zsh
   ./scripts/run_daily_youtube_tasks.sh
   ```

---

- launchd は毎朝 5 時にスクリプトを自動実行します。
- スリープや電源 OFF から復帰した場合も、復帰後に実行されます。
- ログやエラーファイルは `.gitignore` で管理から除外されています。

---

## 実行時の注意（ImportError 対策）

`scripts/` ディレクトリ配下のスクリプトは、
**「スクリプト実行」形式（python scripts/xxx.py）で動作します。**

### ⭕ 正しい例

```sh
python scripts/batch_summarize.py
```

### ❌ パッケージ import 用の実行例（本リポジトリでは不要）

```sh
python -m scripts.batch_summarize
```

> **理由:**
> 本リポジトリの import は「ファイル名のみ」で行っているため、スクリプト実行で十分です。
> 上位階層からのパッケージ import やテスト用途がなければ、-m オプションは不要です。

---

## 注意事項

- Google API キーや OAuth 認証情報（`credentials.json`）が必要です。`.env`や`credentials.json`を適切に用意してください。
- 実行結果やログファイル（`*_log.txt`など）は `.gitignore` で Git 管理対象外になっています。
- 各スクリプトの出力ファイルは上書きされます。必要に応じてバックアップを取ってください。

---

## 2025/05/31 追記: ファイル出力パスの絶対パス化について

- すべての `scripts/` 配下の Python スクリプトで、ファイルの出力・読み込みパスを**絶対パス指定**に統一しました。
  - 例: `os.path.abspath(os.path.join(BASE_DIR, 'xxx.txt'))` のように、プロジェクトルート基準でパスを生成します。
- これにより、どのディレクトリからスクリプトを実行しても、必ず正しい場所にファイルが出力・追記されます。
- launchd や cron など自動実行時や、IDE・ターミナルのカレントディレクトリが異なる場合でも、ファイルの出力先が安定します。
- 以前は相対パス指定だったため、実行ディレクトリによっては意図しない場所にファイルが作成されることがありました。
- 今後は、**必ず絶対パス指定でファイル操作を行う**方針です。

---
