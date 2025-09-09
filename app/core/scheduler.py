from typing import Optional


def setup_schedules(schedules: Optional[str] = None) -> None:
    """APScheduler/cron 連携の土台（スタブ）。

    引数:
        schedules: 例 "19:00,07:00" のような CSV 文字列

    TODO:
    - APScheduler を導入し、アプリ起動時にジョブ登録
    - タイムゾーン対応（Settings.tz を利用）
    - コンフリクト（重複登録）回避とダイナミック更新
    """
    _ = schedules  # いまは未使用
    return None
