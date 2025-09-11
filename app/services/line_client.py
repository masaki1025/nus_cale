from typing import Any, Dict


def send_message(line_user_id: str, message: str) -> Dict[str, Any]:
    """LINE 送信用のラッパ（スタブ）。

    引数:
        line_user_id: 送信先ユーザー ID
        message: 本文

    戻り値:
        送信結果（スタブ）

    備考:
        本実装では実送信しません。将来 LINE Messaging API（push message）で置き換えます。
    """
    return {"ok": True, "user": line_user_id, "message": message}

