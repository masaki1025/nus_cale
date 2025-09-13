from __future__ import annotations

"""
ユーザー設定/回避リスト（「苦手な人」）を扱うリポジトリ層。

- デフォルトでは JSON ファイル（.env: USERS_JSON）に読み書きします。
- 将来的にDBやGoogle Sheetsへ移行する場合も、この層の差し替えで吸収します。
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.config import get_settings
from app.utils.shift_normalize import norm_name


logger = logging.getLogger("app.repositories.user_repo")


def _users_path() -> Path:
    """USERS_JSON のパスを取得する（未設定ならエラー）。"""
    settings = get_settings()
    path = (settings.users_json or "").strip()
    if not path:
        raise RuntimeError("USERS_JSON が未設定です（.env を確認してください）。")
    return Path(path)


def _load_users_source() -> Dict[str, Any]:
    """ユーザー定義（users.json）を読み込み、辞書形式で返す。"""
    p = _users_path()
    if not p.exists():
        logger.warning("USERS_JSON が見つかりません: %s（新規作成想定）", p)
        return {"users": []}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return {"users": data}
        if isinstance(data, dict) and isinstance(data.get("users"), list):
            return data
        # 推測: ルート直下の配列にユーザーが居るケース
        if isinstance(data, dict):
            for v in data.values():
                if isinstance(v, list) and v and isinstance(v[0], dict) and "id" in v[0]:
                    return {"users": v}
        logger.warning("USERS_JSON の形式が想定外です。空として扱います: %s", p)
        return {"users": []}
    except Exception as e:
        logger.exception("USERS_JSON の読み込みに失敗: %s", e)
        return {"users": []}


def _save_users_source(data: Dict[str, Any]) -> None:
    """ユーザー定義を原子的に保存する（tmp→rename）。"""
    p = _users_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    txt = json.dumps(data, ensure_ascii=False, indent=2)
    tmp.write_text(txt, encoding="utf-8")
    try:
        if p.exists():
            p.unlink()
    except Exception:
        pass
    tmp.rename(p)


def _find_user(users: List[Dict[str, Any]], user_id: Optional[str]) -> Optional[Dict[str, Any]]:
    """ユーザー配列から `user_id` に一致する要素を返す。未指定時は先頭。"""
    if not users:
        return None
    if not user_id:
        return users[0]
    sid = str(user_id)
    for u in users:
        if str(u.get("id", "")) == sid:
            return u
    return None


def ensure_user(user_id: str) -> Dict[str, Any]:
    """ユーザーが存在しなければ作成して返す。"""
    data = _load_users_source()
    users: List[Dict[str, Any]] = data.get("users", [])
    user = _find_user(users, user_id)
    if not user:
        user = {"id": str(user_id), "my_name": "", "line_user_id": str(user_id), "avoid_list": []}
        users.append(user)
        data["users"] = users
        _save_users_source(data)
    return user


def load_user_config(user_id: Optional[str]) -> Dict[str, Any]:
    """ユーザー設定を取得する（未指定時はDEFAULT_USER_ID→先頭）。"""
    settings = get_settings()
    data = _load_users_source()
    users: List[Dict[str, Any]] = data.get("users", [])
    target_id = user_id or settings.default_user_id or None
    user = _find_user(users, target_id)
    if not user:
        # 見つからない場合は最低限のダミー
        dummy = {"id": str(target_id or "dummy"), "my_name": "", "line_user_id": "", "avoid_list": []}
        logger.warning("ユーザー設定が見つかりません: id=%s", dummy["id"])
        return dummy
    return {
        "id": user.get("id", ""),
        "my_name": user.get("my_name", ""),
        "line_user_id": user.get("line_user_id", ""),
        "avoid_list": list(user.get("avoid_list", [])),
    }


def load_avoid_list(user_id: Optional[str]) -> List[str]:
    """ユーザーの苦手リスト（avoid_list）を取得する。"""
    cfg = load_user_config(user_id)
    return list(cfg.get("avoid_list", []))


def add_avoid(user_id: str, name: str, max_items: int = 50) -> Dict[str, Any]:
    """苦手リストに追加する。重複は無視し、上限超過はエラーを返す。

    注意: ユーザーが未登録の場合は作成してから追加します。
    """
    data = _load_users_source()
    users: List[Dict[str, Any]] = data.get("users", [])
    user = _find_user(users, user_id)
    if not user:
        user = {"id": str(user_id), "my_name": "", "line_user_id": str(user_id), "avoid_list": []}
        users.append(user)
    avoid = set(user.get("avoid_list", []) or [])
    nname = norm_name(name)
    if nname in avoid:
        return {"ok": True, "message": f"‘{nname}’ は既に登録されています", "count": len(avoid)}
    if len(avoid) >= max_items:
        return {"ok": False, "message": f"上限 {max_items} 件に達しています", "count": len(avoid)}
    avoid.add(nname)
    user["avoid_list"] = sorted(avoid)
    data["users"] = users
    _save_users_source(data)
    return {"ok": True, "message": f"OK: ‘{nname}’ を追加しました", "count": len(user["avoid_list"])}


def remove_avoid(user_id: str, name: str) -> Dict[str, Any]:
    """苦手リストから削除する。未登録時は案内を返す。"""
    data = _load_users_source()
    users: List[Dict[str, Any]] = data.get("users", [])
    user = _find_user(users, user_id)
    if not user:
        return {"ok": False, "message": "ユーザーが存在しません", "count": 0}
    avoid = set(user.get("avoid_list", []) or [])
    nname = norm_name(name)
    if nname not in avoid:
        return {"ok": False, "message": f"‘{nname}’ は見つかりません", "count": len(avoid)}
    avoid.remove(nname)
    user["avoid_list"] = sorted(avoid)
    data["users"] = users
    _save_users_source(data)
    return {"ok": True, "message": f"OK: ‘{nname}’ を削除しました", "count": len(user["avoid_list"])}


def set_my_name(user_id: str, my_name: str) -> Dict[str, Any]:
    """ユーザーの `my_name`（シート上の自分の氏名）を設定する。"""
    data = _load_users_source()
    users: List[Dict[str, Any]] = data.get("users", [])
    user = _find_user(users, user_id)
    if not user:
        user = {"id": str(user_id), "my_name": "", "line_user_id": str(user_id), "avoid_list": []}
        users.append(user)
    user["my_name"] = norm_name(my_name)
    data["users"] = users
    _save_users_source(data)
    return {"ok": True, "message": f"OK: 自分の氏名を ‘{user['my_name']}’ に設定しました"}
