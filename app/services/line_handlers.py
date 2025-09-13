from __future__ import annotations

from typing import Dict, Any, List
import re
from datetime import timedelta

from linebot.v3.messaging import MessagingApi, Configuration, ApiClient
from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage

from app.core.config import get_settings
from app.repositories.user_repo import (
    add_avoid,
    remove_avoid,
    set_my_name,
    ensure_user,
    load_avoid_list,
    load_user_config,
)
from app.repositories.sheet_repo import load_shifts_for_user
from app.utils.time_utils import now_tz


# コマンド正規表現
CMD_ADD = re.compile(r"^\s*苦手追加[\s　]+(.+)$")
CMD_DEL = re.compile(r"^\s*苦手削除[\s　]+(.+)$")
CMD_LIST = re.compile(r"^\s*苦手一覧\s*$")
CMD_SET_NAME = re.compile(r"^\s*設定[\s　]*氏名[\s　]+(.+)$")
CMD_HELP = re.compile(r"^\s*ヘルプ\s*$")
CMD_SHIFT_TOMORROW = re.compile(r"^\s*(明日の勤務|勤務[\s　]*明日)\s*$")
CMD_SHIFT_DATE = re.compile(r"^\s*勤務[\s　]+(\d{4}-\d{2}-\d{2})\s*$")
CMD_NAMES = re.compile(r"^\s*(氏名一覧|メンバー一覧)\s*$")


def _reply_text(reply_token: str, text: str) -> None:
    """テキストで即時返信（reply API, SDK v3）。
    LINE_CHANNEL_ACCESS_TOKEN が未設定の場合は何もしない（開発時の無害化）。
    """
    settings = get_settings()
    token = settings.line_channel_access_token
    if not token:
        return
    config = Configuration(access_token=token)
    with ApiClient(config) as api_client:
        api = MessagingApi(api_client)
        api.reply_message(
            ReplyMessageRequest(reply_token=reply_token, messages=[TextMessage(text=text)])
        )


def _help_text() -> str:
    return (
        "使えるコマンド:\n"
        "- 苦手追加 <氏名>\n"
        "- 苦手削除 <氏名>\n"
        "- 苦手一覧\n"
        "- 設定 氏名 <氏名>\n"
        "- 氏名一覧 / メンバー一覧\n"
        "- 明日の勤務 / 勤務 明日\n"
        "- 勤務 YYYY-MM-DD\n"
        "- ヘルプ"
    )


def handle_follow(event: Dict[str, Any]) -> None:
    """followイベント（友だち登録）を処理し、初期案内を返信する。"""
    user_id = event.get("source", {}).get("userId", "")
    reply_token = event.get("replyToken", "")
    if user_id:
        ensure_user(user_id)
    if reply_token:
        _reply_text(reply_token, "友だち登録ありがとうございます。‘ヘルプ’ と送るとコマンド一覧を表示します。")


def handle_message(event: Dict[str, Any]) -> None:
    """messageイベント（テキスト）を解析し、コマンドを実行して返信する。"""
    user_id = event.get("source", {}).get("userId", "")
    reply_token = event.get("replyToken", "")
    text = (event.get("message", {}) or {}).get("text", "")
    if not reply_token:
        return

    # ヘルプ
    if CMD_HELP.match(text):
        _reply_text(reply_token, _help_text())
        return

    # 苦手追加/削除/一覧
    m = CMD_ADD.match(text)
    if m:
        name = m.group(1).strip()
        res = add_avoid(user_id, name)
        _reply_text(reply_token, f"{res['message']}（合計: {res.get('count', 0)}件）")
        return

    m = CMD_DEL.match(text)
    if m:
        name = m.group(1).strip()
        res = remove_avoid(user_id, name)
        suffix = f"（合計: {res.get('count', 0)}件）" if res.get("ok") else ""
        _reply_text(reply_token, f"{res['message']}{suffix}")
        return

    if CMD_LIST.match(text):
        items = load_avoid_list(user_id)
        if not items:
            _reply_text(reply_token, "苦手リストは空です")
        else:
            joined = ", ".join(items[:50])
            _reply_text(reply_token, f"苦手リスト（{len(items)}件）: {joined}")
        return

    # 氏名設定
    m = CMD_SET_NAME.match(text)
    if m:
        name = m.group(1).strip()
        res = set_my_name(user_id, name)
        _reply_text(reply_token, res["message"])
        return

    # 明日の勤務 or 指定日の勤務
    if CMD_SHIFT_TOMORROW.match(text) or CMD_SHIFT_DATE.match(text):
        # 対象日を決定
        settings = get_settings()
        if CMD_SHIFT_DATE.match(text):
            target_date = CMD_SHIFT_DATE.match(text).group(1)
        else:
            dt = now_tz(settings.tz)
            target_date = (dt + timedelta(days=1)).date().isoformat()

        # 自分の氏名取得
        cfg = load_user_config(user_id)
        my_name = (cfg.get("my_name") or "").strip()
        if not my_name:
            _reply_text(reply_token, "まず ‘設定 氏名 <氏名>’ で自分の氏名を設定してください。")
            return

        # 全体シフト取得（縦持ち）
        rows: List[Dict[str, Any]] = load_shifts_for_user(user_id)
        mine = [r for r in rows if r.get("name") == my_name and r.get("date") == target_date]
        if not mine:
            # ユーザー名が存在するか/日付の範囲をヒント表示
            names = {r.get("name", "") for r in rows}
            if my_name not in names:
                _reply_text(reply_token, f"{target_date} の勤務は未登録です。氏名 ‘{my_name}’ がシートに見つかりません。‘氏名一覧’ で候補を確認し、‘設定 氏名 <氏名>’ を設定してください。")
                return
            dates = sorted({r.get("date", "") for r in rows if r.get("date")})
            hint = f"（利用可能な日付: {dates[0]} ～ {dates[-1]}）" if dates else ""
            _reply_text(reply_token, f"{target_date} の勤務は未登録です。{hint}")
            return

        shift = mine[0].get("shift", "") or "（空）"

        # 要注意の一致（苦手な人）
        avoid = set(load_avoid_list(user_id))
        same = [
            r.get("name")
            for r in rows
            if r.get("date") == target_date and r.get("shift") == shift and r.get("name") != my_name
        ]
        hits = sorted([n for n in same if n in avoid])

        if hits:
            msg = f"{target_date} の勤務: {shift}\n要注意: {', '.join(hits)}"
        else:
            msg = f"{target_date} の勤務: {shift}\n要注意の一致はありません"
        _reply_text(reply_token, msg)
        return

    # シート上の氏名一覧
    if CMD_NAMES.match(text):
        rows = load_shifts_for_user(user_id)
        names = sorted({r.get("name", "") for r in rows if r.get("name")})
        if not names:
            _reply_text(reply_token, "氏名が取得できませんでした。SHEETS_IDやシート内容を確認してください。")
            return
        preview = ", ".join(names[:30])
        suffix = "..." if len(names) > 30 else ""
        _reply_text(reply_token, f"氏名一覧（{len(names)}名）:\n{preview}{suffix}")
        return

    # 未知コマンド
    _reply_text(reply_token, "コマンドが認識できませんでした。‘ヘルプ’ と送ってください。")

