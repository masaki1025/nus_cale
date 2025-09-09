from typing import Any, Dict, List


def load_shifts(sheet_id: str) -> List[Dict[str, Any]]:
    """シフトデータを取得する（スタブ）。

    引数:
        sheet_id: 対象スプレッドシート ID

    戻り値:
        シフトレコードの配列

    TODO:
    - services.sheets_client.fetch_shifts の実装と呼び出し
    - 取得結果のキャッシュ戦略（頻度/スコープ）
    """
    _ = sheet_id
    return []
