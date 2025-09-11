from typing import Optional

from fastapi import APIRouter, Query

from app.services.notify_service import run_notify


router = APIRouter()


@router.post("/jobs/notify", tags=["jobs"]) 
async def notify(user: Optional[str] = Query(default=None)):
    """通知ジョブを手動で実行するエンドポイント（スタブ）。

    引数:
        user: 特定ユーザーのみ通知したい場合に指定（未指定は既定のユーザー）
    """
    result = run_notify(user_id=user)
    return result

