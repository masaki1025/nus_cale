"""環境設定を扱うモジュール。

Settings クラスで .env から環境変数を読み込み、
アプリ全体で利用する設定値を提供します。
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
        """環境変数を読み込み、各種設定値を初期化する。

        TODO:
        - 必須値のバリデーション（空の場合のエラー化、警告ログなど）
        - 機密情報の取り扱い（マスキングログ、外部Secret管理への移行）
        """
        load_dotenv()  # .env があれば読み込む
        self.env = os.getenv("ENV", "development")
        self.port = int(os.getenv("PORT", "8000"))
        self.tz = os.getenv("TZ", "Asia/Tokyo")

        # LINE
        self.line_channel_secret = os.getenv("LINE_CHANNEL_SECRET", "")
        self.line_channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")

        # Google / Sheets
        self.google_project_id = os.getenv("GOOGLE_PROJECT_ID", "")
        self.google_sa_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
        self.sheets_id = os.getenv("SHEETS_ID", "")


@lru_cache
def get_settings() -> Settings:
    """Settings のシングルトンを取得する。

    lru_cache により初回呼び出し時に一度だけインスタンス化し、
    以降は同一インスタンスを返します。

    TODO:
    - 実行時に設定を再読込したい場合（管理APIなど）に備えて、
      キャッシュをクリアするユーティリティを用意する。
    """
    return Settings()
