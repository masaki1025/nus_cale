from datetime import datetime
from zoneinfo import ZoneInfo


def now_tz(tz: str = "Asia/Tokyo") -> datetime:
    """指定タイムゾーンの現在時刻を返す。

    引数:
        tz: IANA タイムゾーン（例: "Asia/Tokyo"）

    TODO:
    - 設定ファイル（Settings.tz）と統一
    - テスト容易性のためのクロック注入（依存性注入）
    """
    return datetime.now(ZoneInfo(tz))
