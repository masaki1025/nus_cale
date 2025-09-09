from typing import Optional

from fastapi import APIRouter, Query

from app.services.notify_service import run_notify


router = APIRouter()


@router.post("/jobs/notify", tags=["jobs"]) 
async def notify(user: Optional[str] = Query(default=None)):
    """通知ジョブを手動起動するエンドポイント（スタブ）。

    引数:
        user: 特定ユーザーのみ通知判定したい場合に指定（未指定で全体想定）

    TODO:
    - 管理用の認可（APIキー等）を付ける
    - 非同期キュー（例: RQ/Celery）またはスケジューラ連携
    - リクエストのトレーシング（ジョブIDの発行）
    """
    result = run_notify(user_id=user)
    return result
