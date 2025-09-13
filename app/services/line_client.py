from typing import Any, Dict
import os

from linebot.v3.messaging import MessagingApi, Configuration, ApiClient
from linebot.v3.messaging.models import PushMessageRequest, TextMessage
try:
    from linebot.v3.exceptions import ApiException as LineApiException
except Exception:
    try:
        from linebot.exceptions import LineBotApiError as LineApiException  # v2 fallback
    except Exception:
        LineApiException = Exception  # 最後の手段

from app.core.config import get_settings


def send_message(line_user_id: str, message: str) -> Dict[str, Any]:
    """LINE Pushメッセージを送信する（SDK v3）。

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

    config = Configuration(access_token=token)
    try:
        with ApiClient(config) as api_client:
            api = MessagingApi(api_client)
            api.push_message(
                PushMessageRequest(
                    to=line_user_id,
                    messages=[TextMessage(text=message)],
                )
            )
        return {"ok": True, "user": line_user_id}
    except LineApiException as e:
        status = getattr(e, "status", None)
        body = getattr(e, "body", None)
        raise RuntimeError(f"LINE push 失敗: status={status} body={body}") from e
