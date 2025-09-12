from typing import Any, Dict
import os

from linebot import LineBotApi
from linebot.models import TextSendMessage
from linebot.exceptions import LineBotApiError

from app.core.config import get_settings


def send_message(line_user_id: str, message: str) -> Dict[str, Any]:
    """LINE Pushメッセージを送信する（SDK実装）。

    引数:
        line_user_id: 送信先ユーザーの userId（Botと友だち状態が必要）
        message: 送信する本文（テキスト）

    戻り値:
        { ok: bool, user: str }

    事前条件:
        - .env もしくは環境変数に LINE_CHANNEL_ACCESS_TOKEN が設定されていること
    """
    settings = get_settings()
    token = settings.line_channel_access_token or os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
    if not token:
        raise RuntimeError("LINE_CHANNEL_ACCESS_TOKEN が未設定です（.env を確認してください）。")

    api = LineBotApi(token)
    try:
        api.push_message(line_user_id, TextSendMessage(text=message))
        return {"ok": True, "user": line_user_id}
    except LineBotApiError as e:
        # SDKの例外には status_code / error 内訳が含まれる
        status = getattr(e, "status_code", None)
        details = getattr(e, "error", None)
        raise RuntimeError(f"LINE push 失敗: status={status} error={details}") from e
