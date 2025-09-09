from fastapi import APIRouter


router = APIRouter()


@router.get("/healthz", tags=["health"])
def healthz():
    """ヘルスチェック用エンドポイント。

    稼働確認やロードバランサのヘルスチェックに利用します。
    """
    return {"status": "ok"}
