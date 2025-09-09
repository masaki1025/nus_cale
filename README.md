# Nus Cale API (FastAPI)

要件定義書（`docs/nus_cale_project.md`）に基づく最小構成の雛形です。

## セットアップ

1. 依存インストール

```bash
pip install -r requirements.txt
```

2. 環境変数

- `.env.example` をコピーして `.env` を作成し、各値を設定してください。

3. 起動

```bash
uvicorn app.main:app --reload --port 8000
```

4. 動作確認

- `GET /healthz` → 200 OK
- `POST /line/webhook` → 200 OK（スタブ）
- `POST /jobs/notify` → 200 OK（スタブ）
- `POST /admin/reload-mapping` → 200 OK（スタブ）

## ディレクトリ

- `app/` FastAPI本体
  - `endpoints/` 主要エンドポイント（health, line, jobs, admin）
  - `core/` 設定・ログ・スケジューラ等の基盤
  - `services/` LINE/Sheetsラッパや判定・通知オーケストレーション
  - `repositories/` データ取得層（ユーザー設定・シート）
  - `models/` Pydanticスキーマ
  - `utils/` 補助関数
- `infra/` Docker/Compose
- `scripts/` 開発用スクリプト

今はスタブ実装です。実ロジックは要件の合意後に段階的に追加してください。
