from fastapi import APIRouter, Body, Header, HTTPException, Request
import hmac
import hashlib
import base64
import json

from app.core.config import get_settings


router = APIRouter()


def _verify_line_signature(secret: str, body_bytes: bytes, signature: str) -> bool:
    mac = hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).digest()
    expected = base64.b64encode(mac).decode("utf-8")
    return hmac.compare_digest(expected, signature)


@router.post("/line/webhook", tags=["line"]) 
async def line_webhook(
    request: Request,
    x_line_signature: str = Header(default="", alias="X-Line-Signature"),
):
    """LINE Webhook の受信エンドポイント。

    - チャネルシークレットで署名検証を行い、正しければ 200 を返す。
    - ここではイベントを記録するのみ（返信などのロジックは未実装）。
    """
    body_bytes = await request.body()
    settings = get_settings()
    secret = settings.line_channel_secret
    if not secret:
        raise HTTPException(status_code=500, detail="LINE_CHANNEL_SECRET が未設定です")
    if not x_line_signature:
        raise HTTPException(status_code=400, detail="X-Line-Signature ヘッダがありません")

    if not _verify_line_signature(secret, body_bytes, x_line_signature):
        raise HTTPException(status_code=401, detail="署名検証に失敗しました")

    try:
        payload = json.loads(body_bytes.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="JSON のパースに失敗しました")

    # 最小限の取り回し（今はログ用に返すのみ）
    events = payload.get("events", []) if isinstance(payload, dict) else []
    # TODO: follow イベントで userId を保存、message イベントでコマンド処理 など
    return {"ok": True, "events": len(events)}
