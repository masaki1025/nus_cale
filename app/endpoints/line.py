from fastapi import APIRouter, Body


router = APIRouter()


@router.post("/line/webhook", tags=["line"]) 
async def line_webhook(payload: dict = Body(...)):
    """LINE Webhook の受信エンドポイント（スタブ）。

    引数:
        payload: LINE プラットフォームから届く生の JSON ペイロード

    備考:
    - 署名検証（チャネルシークレット）は未実装
    - イベント種別（message, follow, postback など）の分岐は未実装
    - 実運用では push 通知連携や状態管理が必要
    """
    return {"ok": True, "received": True}

