from fastapi import APIRouter, Body


router = APIRouter()


@router.post("/line/webhook", tags=["line"]) 
async def line_webhook(payload: dict = Body(...)):
    """LINE Webhook の受信エンドポイント（スタブ）。

    引数:
        payload: LINE プラットフォームから届く生の JSON ペイロード

    TODO:
    - チャネルシークレットを用いた署名検証
    - イベント種別（message, follow, postback など）の分岐実装
    - 返信／プッシュ送信の整理（即時応答と非同期処理の切り分け）
    - リトライと冪等性（重複イベント対策）
    """
    return {"ok": True, "received": True}
