from fastapi import APIRouter


router = APIRouter()


@router.get("/healthz", tags=["health"])
def healthz():
    """簡易ヘルスチェック用エンドポイント。

    監視やロードバランサのヘルスチェックに利用します。
    """
    return {"status": "ok"}

