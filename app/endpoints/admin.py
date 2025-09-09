from fastapi import APIRouter


router = APIRouter()


@router.post("/admin/reload-mapping", tags=["admin"]) 
async def reload_mapping():
    """マッピング設定を再読込する管理系エンドポイント（スタブ）。

    TODO:
    - 設定の永続化場所（ファイル/DB）からの再読込実装
    - 実行ユーザーの認可チェック
    - 再読込に伴うキャッシュクリア（Settings 等）
    """
    return {"ok": True}
