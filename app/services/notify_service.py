from typing import Any, Dict, List, Optional

from app.core.config import get_settings
from app.repositories.user_repo import load_user_config, load_avoid_list
from app.repositories.sheet_repo import load_shifts
from app.services.matching import find_overlaps
from app.services.line_client import send_message


def run_notify(user_id: Optional[str] = None) -> Dict[str, Any]:
    """通知処理（判定→送信）をまとめて実行する（スタブ）。

    引数:
        user_id: 特定ユーザーのみ対象とする場合の識別子（未指定で全体想定）

    戻り値:
        実行結果のサマリ（件数など）

    TODO:
    - pick_my_rows の実装（ユーザー本人の行抽出）
    - 送信済みの重複除去（送信ログの導入）
    - メッセージテンプレート化（日本語/カスタム対応）
    - エラー時のリトライと失敗通知（管理者向け）
    """
    settings = get_settings()

    # ユーザー設定/苦手リスト/シフトを取得（スタブ）
    user_cfg = load_user_config(user_id)
    shifts: List[Dict[str, Any]] = load_shifts(settings.sheets_id)
    my_slots = []  # pick_my_rows(shifts, user_cfg.get("my_name")) 想定
    targets = load_avoid_list(user_id)

    matches = find_overlaps(my_slots, shifts, targets)

    # ヒット時のみ送信（ここではスタブで件数のみ）
    count = len(matches)
    if count > 0 and user_cfg.get("line_user_id"):
        send_message(user_cfg["line_user_id"], f"一致 {count} 件")

    return {"ok": True, "matched": count, "user": user_id}
