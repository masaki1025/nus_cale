from typing import Any, Dict, List, Optional
import csv
import json
import os
import re

import gspread
from google.oauth2.service_account import Credentials

from app.core.config import get_settings


def _build_credentials(sa_json: str, scopes: List[str]) -> Credentials:
    """サービスアカウント情報（ファイルパス or JSON文字列）から認証情報を作成します。"""
    if not sa_json:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON が未設定です（.env を確認してください）。")

    # ファイルとして存在する場合
    if os.path.isfile(sa_json):
        return Credentials.from_service_account_file(sa_json, scopes=scopes)

    # JSON文字列として扱う
    try:
        info = json.loads(sa_json)
        if not isinstance(info, dict):
            raise ValueError("not a dict")
        return Credentials.from_service_account_info(info, scopes=scopes)
    except Exception as e:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON が不正です（パスまたはJSONを設定してください）。") from e


def _load_csv(path: str) -> List[Dict[str, Any]]:
    """ローカルの CSV を読み込み、ヘッダー行をキーにした辞書配列を返します。"""
    rows: List[Dict[str, Any]] = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    return rows


def fetch_shifts(sheet_id: str, worksheet_title: Optional[str] = None, worksheet_gid: Optional[int] = None) -> List[Dict[str, Any]]:
    """シフト行を取得します（Google Sheets またはローカルCSV）。

    - `SHEETS_ID` が Google スプレッドシートの ID の場合 → Google Sheets から取得
    - `SHEETS_ID` がローカルの CSV パスの場合（例: `sheet/data.csv`）→ CSV から取得
    """
    if not sheet_id:
        raise RuntimeError("SHEETS_ID が未設定です（.env を確認してください）。")

    # ローカルCSVパスとして存在するなら優先して読み込む
    if os.path.isfile(sheet_id) and sheet_id.lower().endswith(".csv"):
        return _load_csv(sheet_id)

    # それ以外は Google Sheets ID として扱う
    settings = get_settings()
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
    ]
    creds = _build_credentials(settings.google_sa_json, scopes)

    try:
        client = gspread.authorize(creds)
        def _extract_sheet_key(value: str) -> str:
            m = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", value)
            return m.group(1) if m else value
        spreadsheet = client.open_by_key(_extract_sheet_key(sheet_id))
        # ワークシート選択: タイトル > GID > 先頭（旧実装より前に早期リターン）
        try:
            ws = None
            # Settings からの指定を使う場合は repository 層で渡す想定
            if 'worksheet_title' in locals() and worksheet_title:
                ws = spreadsheet.worksheet(worksheet_title)
            elif 'worksheet_gid' in locals() and worksheet_gid is not None:
                get_by_id = getattr(spreadsheet, "get_worksheet_by_id", None)
                if callable(get_by_id):
                    ws = get_by_id(int(worksheet_gid))
                else:
                    for _ws in spreadsheet.worksheets():
                        if getattr(_ws, "id", None) == int(worksheet_gid):
                            ws = _ws
                            break
            if ws is None:
                ws = spreadsheet.sheet1
            rows: List[Dict[str, Any]] = ws.get_all_records()
            return rows
        except Exception:
            # 失敗時は従来の先頭シート取得にフォールバック（下のコードへ）
            pass
        worksheet = spreadsheet.sheet1  # 先頭シートを使用（必要に応じて変更）
        rows: List[Dict[str, Any]] = worksheet.get_all_records()
        return rows
    except gspread.SpreadsheetNotFound as e:
        raise RuntimeError("指定の SHEETS_ID のスプレッドシートが見つかりません。共有設定を確認してください。") from e
    except gspread.exceptions.APIError as e:
        raise RuntimeError("Google Sheets API エラーが発生しました。API有効化・権限を確認してください。") from e
    except Exception as e:
        raise RuntimeError("シート取得中に予期せぬエラーが発生しました。") from e
