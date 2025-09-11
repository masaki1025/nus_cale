from __future__ import annotations

"""
ユーザー設定/回避リストを扱うリポジトリ層。

デフォルトでは JSON ファイル（.env: USERS_JSON）から読み取ります。
将来的にDBやGoogle Sheetsへ移行する場合も、この層の実装差し替えで吸収します。
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.config import get_settings


logger = logging.getLogger("app.repositories.user_repo")


def _load_users_source() -> Dict[str, Any]:
    """ユーザー定義のデータソースを読み込む。

    期待フォーマット（いずれか）:
    - { "users": [ {"id":"...", "my_name":"...", "line_user_id":"...", "avoid_list":[...]} , ... ] }
    - [ {"id":"...", ...}, ... ]  # ルートが配列でも許容
    なければ空の構造を返す。
    """
    settings = get_settings()
    path = (settings.users_json or "").strip()
    if not path:
        logger.warning("USERS_JSON が未設定です。ダミー設定で動作します。")
        return {"users": []}
    p = Path(path)
    if not p.exists():
        logger.warning("USERS_JSON が見つかりません: %s", p)
        return {"users": []}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return {"users": data}
        if isinstance(data, dict):
            # usersキーが無ければ推測して補完
            if "users" in data and isinstance(data["users"], list):
                return data
            # idなどを含む配列が on-disk root にあるケース
            for k, v in data.items():
                if isinstance(v, list) and v and isinstance(v[0], dict) and "id" in v[0]:
                    return {"users": v}
            # どれでもなければ空
        logger.warning("USERS_JSON の形式が想定外です。空として扱います: %s", p)
        return {"users": []}
    except Exception as e:
        logger.exception("USERS_JSON の読み込みに失敗: %s", e)
        return {"users": []}


def _find_user(users: List[Dict[str, Any]], user_id: Optional[str]) -> Optional[Dict[str, Any]]:
    """ユーザー配列から user_id に一致する要素を返す。未指定時は先頭を返す。"""
    if not users:
        return None
    if not user_id:
        return users[0]
    for u in users:
        if str(u.get("id", "")) == str(user_id):
            return u
    return None


def load_user_config(user_id: Optional[str]) -> Dict[str, Any]:
    """ユーザーの設定を取得する（JSONベース）。

    引数:
        user_id: ユーザー識別子（未指定時は .env の DEFAULT_USER_ID → 先頭の順）

    戻り値:
        ユーザー設定（氏名、LINEユーザーID など）
    """
    settings = get_settings()
    data = _load_users_source()
    users: List[Dict[str, Any]] = data.get("users", [])
    target_id = user_id or settings.default_user_id or None
    user = _find_user(users, target_id)
    if not user:
        # ダミーを返す（後段が動作できるよう最低限）
        dummy = {
            "id": target_id or "dummy",
            "my_name": "未設定",
            "line_user_id": "",
            "avoid_list": [],
        }
        logger.warning("ユーザー設定が見つかりません。ダミーを返します: id=%s", dummy["id"])
        return dummy
    # 正規化（必須キーの存在保証）
    return {
        "id": user.get("id", ""),
        "my_name": user.get("my_name", ""),
        "line_user_id": user.get("line_user_id", ""),
        "avoid_list": list(user.get("avoid_list", [])),
    }


def load_avoid_list(user_id: Optional[str]) -> List[str]:
    """ユーザーの回避リスト（苦手な人の一覧）を取得する。"""
    cfg = load_user_config(user_id)
    return list(cfg.get("avoid_list", []))

