from fastapi import APIRouter, Depends
from app.core.config import get_settings
from app.core.scheduler import (
    setup_schedules,
    shutdown_schedules,
    is_scheduler_running,
    get_jobs_info,
)
from app.core.security import require_admin


router = APIRouter(dependencies=[Depends(require_admin)])


@router.post("/admin/reload-mapping", tags=["admin"]) 
async def reload_mapping():
    """マッピング設定の再読込を行う管理エンドポイント（スタブ）。"""
    return {"ok": True}


@router.post("/admin/reload-settings", tags=["admin"]) 
async def reload_settings():
    """.env の再読込とスケジューラ再設定を行う管理エンドポイント。

    - get_settings の lru_cache をクリアして再生成
    - スケジューラを停止→必要に応じて再起動（NOTIFY_SCHEDULES が設定されている場合）
    - 反映後の主要設定とジョブ情報を返す
    """
    # 設定の再読込
    get_settings.cache_clear()
    settings = get_settings()

    # スケジューラの再設定
    shutdown_schedules(wait=False)
    if settings.notify_schedules:
        setup_schedules(settings.notify_schedules)

    return {
        "ok": True,
        "env": settings.env,
        "tz": settings.tz,
        "notify_schedules": settings.notify_schedules,
        "scheduler_running": is_scheduler_running(),
        "jobs": get_jobs_info(),
    }
