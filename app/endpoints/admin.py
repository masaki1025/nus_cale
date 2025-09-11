from fastapi import APIRouter


router = APIRouter()


@router.post("/admin/reload-mapping", tags=["admin"]) 
async def reload_mapping():
    """マッピング設定の再読込を行う管理エンドポイント（スタブ）。"""
    return {"ok": True}

