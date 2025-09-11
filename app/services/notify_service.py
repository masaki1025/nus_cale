from typing import Any, Dict, List, Optional

from app.core.config import get_settings
from app.repositories.user_repo import load_user_config, load_avoid_list
from app.repositories.sheet_repo import load_shifts_for_user
from app.services.matching import find_overlaps, pick_my_rows
from app.services.line_client import send_message


def _format_message(user_name: str, events: List[Dict[str, Any]]) -> str:
    """通知メッセージ本文を整形する。"""
    if not events:
        return f"{user_name}: 要注意の一致はありません"
    lines = [f"{user_name} さんの要注意一致:"]
    for e in events:
        lines.append(f"- {e['date']} {e['shift']}: 一緒 {', '.join(e.get('with', []))}")
    return "\n".join(lines)


def run_notify(user_id: Optional[str] = None) -> Dict[str, Any]:
    """通知処理（取得→判定→送信）を実行する。

    引数:
        user_id: 特定ユーザーのみ通知したい場合の識別子（未指定は既定のユーザー）

    戻り値:
        実行結果のサマリ（件数など）
    """
    settings = get_settings()

    # ユーザー設定/回避リスト/シフト（縦持ち: name/date/shift）を取得
    user_cfg = load_user_config(user_id)
    shifts: List[Dict[str, Any]] = load_shifts_for_user(user_id)
    my_slots = pick_my_rows(shifts, user_cfg.get("my_name", ""))
    targets = load_avoid_list(user_id)

    events = find_overlaps(my_slots, shifts, targets)
    count = len(events)

    # メッセージ組立て
    message = _format_message(user_cfg.get("my_name", ""), events)

    # ヒット時のみ push（現状はスタブ送信）
    if count > 0 and user_cfg.get("line_user_id"):
        send_message(user_cfg["line_user_id"], message)

    return {"ok": True, "matched": count, "user": user_id, "message": message}
