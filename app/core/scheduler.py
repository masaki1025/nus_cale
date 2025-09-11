

"""
APScheduler を用いた定期実行のセットアップ/停止ユーティリティ。

- NOTIFY_SCHEDULES（例: "19:00,07:00"）を解析し、指定時刻に通知ジョブを登録
- タイムゾーンは Settings.tz（例: Asia/Tokyo）を使用
- 重複実行防止や取りこぼし緩和のオプションを設定
"""
from __future__ import annotations
import logging
import os
from typing import List, Optional, Tuple

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo

from app.core.config import get_settings
from app.services.notify_service import run_notify


logger = logging.getLogger("app.scheduler")

_scheduler: Optional[AsyncIOScheduler] = None


def _parse_schedules(spec: Optional[str]) -> List[Tuple[int, int]]:
    """時刻CSV文字列を (hour, minute) の配列に変換する。

    - 入力例: "19:00,07:00"
    - バリデーション: フォーマット不正や範囲外はスキップ
    - 出力: 重複排除し、(hour, minute) を昇順で返す
    """
    times: List[Tuple[int, int]] = []
    if not spec:
        return times
    for token in spec.split(","):
        token = token.strip()
        if not token:
            continue
        if ":" not in token:
            logger.warning("無効な時刻形式をスキップ: %s", token)
            continue
        h_str, m_str = token.split(":", 1)
        try:
            h = int(h_str)
            m = int(m_str)
            if not (0 <= h <= 23 and 0 <= m <= 59):
                raise ValueError
        except ValueError:
            logger.warning("無効な時刻をスキップ: %s", token)
            continue
        times.append((h, m))
    # 重複排除 + ソート
    return sorted(set(times))


def _notify_job() -> None:
    """定期通知ジョブの本体処理。

    - app.services.notify_service.run_notify(user=None) を呼び出す
    - 結果をINFOログ、例外はERRORログに出力
    """
    try:
        result = run_notify(user_id=None)
        logger.info("通知ジョブ実行: %s", result)
    except Exception as e:
        logger.exception("通知ジョブで例外: %s", e)


def setup_schedules(schedules: Optional[str] = None) -> None:
    """APScheduler を初期化し、通知ジョブを設定・起動する。

    引数:
        schedules: 例 "19:00,07:00" のような CSV 時刻列（未指定時は Settings.notify_schedules/環境変数）

    注意:
    - タイムゾーンは Settings.tz を使用（ZoneInfo）
    - coalesce=True で遅延時は直近1回にまとめる
    - max_instances=1 で重複実行を防止
    - misfire_grace_time=60 で取りこぼしに猶予
    - 既に起動済みの場合は二重起動しない
    """
    global _scheduler
    if _scheduler is not None:
        logger.debug("スケジューラは既に起動済み")
        return

    settings = get_settings()
    tz = ZoneInfo(settings.tz)
    spec = schedules or getattr(settings, "notify_schedules", None) or os.getenv("NOTIFY_SCHEDULES", "")
    times = _parse_schedules(spec)
    if not times:
        logger.warning("スケジュール時刻が未設定のため、スケジューラは起動しません（NOTIFY_SCHEDULES などを設定）")
        return

    scheduler = AsyncIOScheduler(
        job_defaults=dict(coalesce=True, max_instances=1, misfire_grace_time=60),
        timezone=tz,
    )
    for h, m in times:
        trigger = CronTrigger(hour=h, minute=m, timezone=tz)
        job_id = f"notify-{h:02d}{m:02d}"
        scheduler.add_job(_notify_job, trigger=trigger, id=job_id, replace_existing=True)
        logger.info("通知ジョブを登録: %02d:%02d (%s)", h, m, job_id)

    scheduler.start()
    _scheduler = scheduler
    for job in scheduler.get_jobs():
        logger.info("ジョブ登録済み: id=%s next_run=%s", job.id, job.next_run_time)


def shutdown_schedules(wait: bool = False) -> None:
    """スケジューラを停止する。

    引数:
        wait: True の場合、実行中ジョブの終了を待ってから停止
    """
    global _scheduler
    if _scheduler is None:
        return
    try:
        _scheduler.shutdown(wait=wait)
        logger.info("スケジューラを停止しました")
    finally:
        _scheduler = None
