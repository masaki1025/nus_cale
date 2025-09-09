from typing import Any, Dict


def send_message(line_user_id: str, message: str) -> Dict[str, Any]:
    """LINE 送信用のラッパ（スタブ）。

    引数:
        line_user_id: 送信先ユーザー ID
        message: 本文

    戻り値:
        送信結果（スタブ）

    TODO:
    - LINE Messaging API（push message）実装
    - アクセストークン管理とリトライ（429/5xx）
    - 監査ログ（送信ログの永続化）
    """
    return {"ok": True, "user": line_user_id, "message": message}
