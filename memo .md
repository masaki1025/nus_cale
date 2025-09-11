FastAPIでAPIサーバを構成し、Googleシートからシフトを取得→「苦手な人」との勤務一致を判定→必要に応じてLINE通知する流れ。

設定は.env→app/core/config.pyのSettingsに集約。層は「core / repositories / services / endpoints」で分離。
主要コンポーネント

core
<!-- app/core/config.py: .env読込。SHEETS_ID, GOOGLE_SERVICE_ACCOUNT_JSON, LINE_*, TZなど。 -->
<!-- app/core/scheduler.py: 定期実行の枠（現状スタブ）。 -->
app/core/logging.py: ログ初期化（必要に応じて使用）。
repositories
<!-- app/repositories/sheet_repo.py: シフト取得の倉庫係（実体はservicesへ委譲）。 -->
<!-- app/repositories/user_repo.py: ユーザー設定/回避リストの取得（現状スタブ。将来DB/Sheets等へ）。 -->
services
<!-- app/services/sheets_client.py: Google Sheets/ローカルCSVからシフト行を取得。 -->
<!-- app/services/matching.py: 勤務一致判定（現状スタブ）。 -->
<!-- app/services/notify_service.py: 通知実行のオーケストレーション。 -->
app/services/line_client.py: LINE送信のスタブ（Push実装は今後差し替え）。
endpoints
app/endpoints/health.py: ヘルスチェック。
app/endpoints/line.py: LINE Webhook受信（現状スタブ。署名検証など今後）。
app/endpoints/jobs.py: /jobs/notifyで通知バッチを手動起動。
app/endpoints/admin.py: 設定リロードなどの管理操作（スタブ）。
エントリ
app/main.py: FastAPIアプリ生成・ルータ登録。
データフロー（通知まで）

設定読込: get_settings()が.envを読み環境変数を反映（シートID/LINEトークン/SA JSON/TZ）。
シフト取得: sheet_repo.load_shifts()→services/sheets_client.fetch_shifts()。
SHEETS_IDがCSVパスならローカルCSVを読み込み、そうでなければGoogle Sheets APIで取得。
ユーザー情報: user_repo.load_user_config()でユーザーの氏名/LINEユーザーID、load_avoid_list()で「苦手な人」一覧を取得（現状スタブ）。
一致判定: services/matching.find_overlaps()で「同一日・同一勤務帯」の一致を抽出（実装要）。
通知: 一致があればservices/line_client.send_message()でLINEに送信（スタブを実装置き換え予定）。
実行I/F:
API: POST /jobs/notify（クエリ?user=...で対象ユーザー指定可）
Webhook: POST /line/webhook（将来、対話UIや設定変更に対応）
定期: core/scheduler.pyで毎日実行に拡張予定
起動と実行

サーバ起動（開発）: uvicorn app.main:app --reload
手動通知起動: curl -X POST 'http://localhost:8000/jobs/notify?user=ユーザーID'
ヘルスチェック: GET /healthz
設定（.env例）

SHEETS_ID: GoogleシートID もしくは ローカルCSVパス
GOOGLE_SERVICE_ACCOUNT_JSON: サービスアカウントJSON（パス or JSON文字列）
LINE_CHANNEL_SECRET, LINE_CHANNEL_ACCESS_TOKEN: LINEチャネル情報
TZ: 例 Asia/Tokyo
ローカルCSVとクレンジング

アプリ側はservices/sheets_client._load_csv()でUTF-8/ヘッダー付のCSVを期待。
もしCSVの整形/正規化が必要なら、scripts/直下のツール（scripts/gogle/data_clean.py など）で事前にクリーン化してからSHEETS_IDにそのパスを指定。
未実装/今後のTODO（主要）

services/matching.find_overlaps: 実ロジック（「日勤/準夜/深夜/公休」などのキー正規化→一致判定）
services/line_client.send_message: LINE Push実装（公式SDK or 既存scripts/line_/push.py相当を移植）
user_repo: 永続化実装（DB/Sheets/ファイル）とLINEユーザーID⇔氏名のマッピング
line.py: 署名検証・イベント種別（message/follow/postback）処理・対話コマンド
scheduler.py: APScheduler/cron連携で前日19:00/当日7:00などの定期実行
例外/リトライ・監視ログの整備
この設計で、APIからも定期実行からも同じサービス群を呼び出す構造になっています。必要であれば、マッチング仕様（勤務帯キーや一致条件の詳細）を詰め、実装まで進めます。