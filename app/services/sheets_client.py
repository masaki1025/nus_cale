from typing import Any, Dict, List


def fetch_shifts(sheet_id: str) -> List[Dict[str, Any]]:
    """Google Sheets からシフトを取得する（スタブ）。

    引数:
        sheet_id: 対象スプレッドシート ID

    戻り値:
        行ごとのレコード配列（アプリ内の共通形式に正規化予定）

    TODO:
    - Sheets API / gspread での実データ取得
    - マッピング設定に基づく正規化（列→日付/帯/氏名 等）
    - レート制限・ネットワークエラーのリトライ
    """
    return []
