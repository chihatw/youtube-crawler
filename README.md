# youtube_crawler.py

`youtube_crawler.py` は Automator で使用するための Python スクリプトです。  
「取得片名.app」で利用されています。

## 使い方

1. 仮想環境を有効化  
   （初回のみ仮想環境を作成してください）

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
