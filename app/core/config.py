"""
アプリ共通の設定読み込みモジュール。

Settings クラスが .env から環境変数を読み込み、
アプリ全体で参照する設定値を保持します。
"""

from functools import lru_cache
import os
from dotenv import load_dotenv


class Settings:
    """アプリケーションの設定値を保持するクラス。

    - .env（存在すれば）から環境変数を読み込み、属性として保持します。
    - ここで扱う値は FastAPI アプリ起動時やサービス層で参照します。
    """

    def __init__(self) -> None:
        """環境変数を読み込み、各種設定値を初期化します。"""
        load_dotenv()  # .env があれば読み込む
        self.env = os.getenv("ENV", "development")
        self.port = int(os.getenv("PORT", "8000"))
        self.tz = os.getenv("TZ", "Asia/Tokyo")
        # 通知スケジュール（例: "19:00,07:00"）。未設定ならスケジューラは起動しない。
        self.notify_schedules = os.getenv("NOTIFY_SCHEDULES", "")

        # LINE
        self.line_channel_secret = os.getenv("LINE_CHANNEL_SECRET", "")
        self.line_channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")

        # Google / Sheets
        self.google_project_id = os.getenv("GOOGLE_PROJECT_ID", "")
        self.google_sa_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
        self.sheets_id = os.getenv("SHEETS_ID", "")
        # 任意: ワークシート指定（タイトルまたはgid）
        self.sheets_worksheet_title = os.getenv("SHEETS_WORKSHEET_TITLE", "")
        self.sheets_gid = os.getenv("SHEETS_GID", "")

        # Users（ユーザー設定/回避リストの保管先）
        # JSONファイルパスを推奨（例: app/data/users.json）
        self.users_json = os.getenv("USERS_JSON", "")
        self.default_user_id = os.getenv("DEFAULT_USER_ID", "")

        # Admin（管理系エンドポイントの保護用）
        self.admin_api_key = os.getenv("ADMIN_API_KEY", "")


@lru_cache
def get_settings() -> Settings:
    """Settings のシングルトンを取得する。

    lru_cache により初回呼び出し時に一度だけインスタンス化し、
    以降は同一インスタンスを返します。
    """
    return Settings()
