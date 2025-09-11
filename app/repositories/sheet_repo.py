"""
シフトデータ取得用のリポジトリ層。

- データ源（Google Sheets またはローカルCSV）を意識せずに呼び出せる薄いラッパー。
- 実際の取得処理は services.sheets_client に委譲します。
"""

from typing import Any, Dict, List, Optional
import logging

from app.core.config import get_settings
from app.services.sheets_client import fetch_shifts
from app.repositories.user_repo import load_user_config
from app.utils.shift_normalize import normalize_to_long


logger = logging.getLogger("app.repositories.sheet_repo")

Row = Dict[str, Any]


def load_shifts(sheet_id: str) -> List[Row]:
    """シフトデータを取得する。

    引数:
        sheet_id: Google スプレッドシートのID もしくは ローカルCSVのパス

    戻り値:
        行ディクショナリの配列（ヘッダー行をキーとする）

    例外:
        RuntimeError: 認証・権限・ネットワーク等の失敗時（下層からの例外をラップ）
    """
    try:
        rows = fetch_shifts(sheet_id)
        rows = normalize_to_long(rows)
        logger.info("シフト取得: rows=%d source=%s", len(rows), sheet_id)
        return rows
    except Exception as e:
        logger.exception("シフト取得に失敗しました: %s", e)
        raise


def load_shifts_from_settings() -> List[Row]:
    """Settings からシートID/CSVパスを読み、シフトデータを取得する。

    .env の `SHEETS_ID` を参照し、Google Sheets またはローカルCSVから取得します。
    """
    settings = get_settings()
    if not settings.sheets_id:
        raise RuntimeError("SHEETS_ID が未設定です。Google SheetsのIDまたはCSVパスを .env に設定してください。")
    # 任意のワークシート指定（タイトル or GID）
    title = (settings.sheets_worksheet_title or "").strip()
    gid_val = (settings.sheets_gid or "").strip()
    gid: Optional[int] = None
    if gid_val:
        try:
            gid = int(gid_val)
        except ValueError:
            logger.warning("SHEETS_GID が数値ではありません: %s", gid_val)
    try:
        rows = fetch_shifts(settings.sheets_id, worksheet_title=title or None, worksheet_gid=gid)
        rows = normalize_to_long(rows)
        return rows
    except Exception:
        # 失敗した場合はタイトル/GIDを無視して先頭シートにフォールバック
        logger.warning("指定ワークシートの取得に失敗。先頭シートへフォールバックします")
        rows = fetch_shifts(settings.sheets_id)
        rows = normalize_to_long(rows)
        return rows


def load_shifts_for_user(user_id: Optional[str]) -> List[Row]:
    """ユーザーごとの設定を優先してシフトデータを取得する。

    優先順位:
    1) users.json の各ユーザー設定（sheets_id / worksheet_title / gid）
    2) .env のグローバル設定（SHEETS_ID / SHEETS_WORKSHEET_TITLE / SHEETS_GID）
    いずれも無い場合は例外。
    """
    settings = get_settings()
    user = load_user_config(user_id)

    eff_sheet_id = (str(user.get("sheets_id", "")) or settings.sheets_id or "").strip()
    if not eff_sheet_id:
        raise RuntimeError("ユーザーとグローバルのどちらにも SHEETS_ID が設定されていません")

    eff_title = (str(user.get("worksheet_title", "")) or settings.sheets_worksheet_title or "").strip()
    gid_raw = user.get("gid") if user.get("gid") is not None else settings.sheets_gid
    eff_gid: Optional[int] = None
    if gid_raw not in (None, ""):
        try:
            eff_gid = int(gid_raw)
        except (TypeError, ValueError):
            logger.warning("gid の値が数値として無効です: %s", gid_raw)

    try:
        rows = fetch_shifts(eff_sheet_id, worksheet_title=eff_title or None, worksheet_gid=eff_gid)
        rows = normalize_to_long(rows)
        return rows
    except Exception:
        logger.warning("ユーザー優先のワークシート取得に失敗。先頭シートへフォールバックします")
        rows = fetch_shifts(eff_sheet_id)
        rows = normalize_to_long(rows)
        return rows
