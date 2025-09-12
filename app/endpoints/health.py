from fastapi import APIRouter, Response
from app.core.config import get_settings
from app.core.scheduler import is_scheduler_running, get_jobs_info


router = APIRouter()


@router.get("/healthz", tags=["health"])
def healthz():
    """簡易ヘルスチェック用エンドポイント。

    監視やロードバランサのヘルスチェックに利用します。
    """
    return {"status": "ok"}


@router.get("/readyz", tags=["health"])
def readyz() -> Response:
    """準備完了（readiness）チェック。

    判定基準（最低限）:
    - SHEETS_ID が設定されていること
    - NOTIFY_SCHEDULES が設定されている場合はスケジューラが起動中であること
    LINEトークン等は任意（Pushを使わない運用も想定）
    """
    settings = get_settings()
    sheets_config = bool(settings.sheets_id)
    schedules_required = bool(settings.notify_schedules)
    scheduler_ok = is_scheduler_running() if schedules_required else True

    ok = sheets_config and scheduler_ok
    body = {
        "ok": ok,
        "sheets_config": sheets_config,
        "scheduler_required": schedules_required,
        "scheduler_running": is_scheduler_running(),
        "scheduler_jobs": get_jobs_info(),
    }
    status_code = 200 if ok else 503
    return Response(content=__import__("json").dumps(body, ensure_ascii=False), media_type="application/json", status_code=status_code)
