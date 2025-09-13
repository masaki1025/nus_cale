# Nus Cale API (FastAPI)

シフト情報（Google Sheets またはローカル CSV）と LINE Messaging API を連携する FastAPI アプリです。

- LINE テキストコマンドでの操作（氏名設定・苦手リスト管理・シフト照会）
- 「氏名一覧/メンバー一覧」の取得
- スケジューラにより毎日 07:00 / 19:00 に要注意（苦手な人との同番）を通知

## 主要機能

- ユーザーごとの設定・苦手（回避）リストの管理（`app/data/users.json`）
- Google Sheets または CSV からシフト取得（`SHEETS_ID`）
- コマンド例（LINE で送信）:
  - `苦手追加 <氏名>` / `苦手削除 <氏名>` / `苦手一覧`
  - `設定 氏名 <氏名>`（自分の氏名を設定）
  - `氏名一覧` / `メンバー一覧`
  - `明日の勤務` / `勤務 明日` / `勤務 YYYY-MM-DD`
  - `ヘルプ`

## ディレクトリ構成（抜粋）

- `app/main.py`: FastAPI アプリ起動、スケジューラの起動/停止
- `app/core/`
  - `config.py`: `.env` を読み込む設定クラス
  - `scheduler.py`: APScheduler による定期通知ジョブ
- `app/endpoints/`: ルータ定義（`health.py`, `line.py`, `jobs.py`, `admin.py`）
- `app/services/`
  - `line_handlers.py`: LINE Webhook メッセージのコマンド処理
  - `notify_service.py`: 通知ロジック（重複・要注意の検出と Push）
  - `line_client.py`: LINE Push API クライアント
  - `sheets_client.py`: Sheets/CSV 取得クライアント
- `app/repositories/`：設定やシフトのリポジトリ層
- `app/utils/`：時刻・シフト正規化などのユーティリティ

## セットアップ

前提: Python 3.10+ 推奨、仮想環境の使用を推奨します。

1) 依存関係のインストール

`pip install -r requirements.txt`

2) `.env` の作成（主要項目）

- `ENV`: 例 `development`
- `PORT`: 例 `8000`
- `TZ`: タイムゾーン。例 `Asia/Tokyo`
- `LINE_CHANNEL_SECRET`, `LINE_CHANNEL_ACCESS_TOKEN`: LINE チャネルの資格情報
- `GOOGLE_SERVICE_ACCOUNT_JSON`: サービスアカウント JSON（ファイルパス or JSON 文字列）
- `SHEETS_ID`: 取得対象（スプレッドシート ID / URL / ローカル CSV パス）
- `SHEETS_WORKSHEET_TITLE`, `SHEETS_GID`: 任意。特定のタブを指定する場合
- `NOTIFY_SCHEDULES`: 例 `"19:00,07:00"`（JST、順不同で可）
- `USERS_JSON`: ユーザー設定ファイルパス（例 `app/data/users.json`）
- `ADMIN_API_KEY`: 管理系 API 用のトークン

3) ユーザー設定（`USERS_JSON`）

`app/data/users.json_sample` を参考に作成します（例）。

```
{
  "users": [
    {
      "id": "alice",
      "my_name": "佐藤美咲",
      "line_user_id": "Uxxxxxxxx_alice",
      "avoid_list": ["鈴木花", "中村結衣"]
    }
  ]
}
```

4) シートデータの準備

- ローカル CSV の場合は `SHEETS_ID=sheet/2025_9__with_summary.csv` のようにパスを指定（UTF-8 / UTF-8 BOM 可）。
- Google Sheets の場合は、対象シートをサービスアカウントの `client_email` に共有してください。
- 横持ち（1 列目=氏名、列名=YYYY-MM-DD）または縦持ち（name/date/shift）に対応しています。

## 起動と確認

- アプリ起動: `uvicorn app.main:app --reload --port 8000`
- ヘルス: `GET /healthz` が 200
- 準備完了: `GET /readyz` で `scheduler_jobs` と次回実行時刻を確認

## スケジューラと通知

- APScheduler により、`NOTIFY_SCHEDULES` で指定した時刻（例 `07:00` と `19:00`）にジョブ実行。
- 重複・取りこぼしの緩和設定（`coalesce=True`, `misfire_grace_time=60`）。
- 通知送信は「要注意の一致がある場合のみ」Push します（一致なしのときは Push しません）。
  - 一致なしでも通知したい場合は `app/services/notify_service.py` の送信条件を調整してください。

## エンドポイント

- `GET /healthz`: 簡易ヘルスチェック
- `GET /readyz`: Sheets 設定とスケジューラ状態を返却
- `POST /line/webhook`: LINE Webhook 受信（`X-Line-Signature` で署名検証）
  - text メッセージ: 各コマンドを処理
  - follow イベント: 初回案内を返信
- `POST /jobs/notify?user=<id>`: 通知ジョブの手動実行（即時テスト用）
- 管理系（要 `X-Admin-Token` ヘッダ）
  - `POST /admin/reload-settings`: `.env` 再読込とスケジューラ再設定
  - `POST /admin/reload-mapping`: スタブ

## LINE コマンド一覧

- 苦手追加 `<氏名>` / 苦手削除 `<氏名>` / 苦手一覧
- 設定 氏名 `<氏名>`（シート上の自分の氏名）
- 氏名一覧 / メンバー一覧（シート上の氏名プレビュー）
- 明日の勤務 / 勤務 明日
- 勤務 `YYYY-MM-DD`
- ヘルプ

## よくある問題と対処

- 「氏名が取得できませんでした」: `SHEETS_ID`、シート内容、サービスアカウント共有を確認。
- 「勤務が未登録」: `設定 氏名` の氏名がシートに存在するか、`氏名一覧/メンバー一覧` で候補を確認。
- 通知が来ない: `NOTIFY_SCHEDULES` と `TZ` を確認。`/readyz` でジョブ登録/次回実行時刻を確認。
- LINE Push 失敗: `LINE_CHANNEL_ACCESS_TOKEN` と `users.json` の `line_user_id` を確認。

## 依存関係

- FastAPI, Uvicorn, APScheduler, python-dotenv
- gspread, google-auth（Google Sheets 用）
- line-bot-sdk >= 3.17.0, < 4（LINE SDK v3 系）
- Windows の場合 tzdata（`requirements.txt` で自動）

---

必要に応じて機能拡張（通知条件やメッセージ形式など）にも対応します。
