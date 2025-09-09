from typing import Any, Dict, List, Optional


def load_user_config(user_id: Optional[str]) -> Dict[str, Any]:
    """ユーザーの設定を取得する（スタブ）。

    引数:
        user_id: ユーザー識別子（未指定時はダミー）

    戻り値:
        ユーザー設定（氏名、LINEユーザーID 等）

    TODO:
    - 永続化層（DB/Sheets）との接続実装
    - 氏名の別名管理（Aliases）
    - 個人情報の保護（最小権限でのアクセス）
    """
    return {
        "id": user_id or "dummy",
        "my_name": "山田太郎",
        "line_user_id": "Uxxxxxxxx",
    }


def load_avoid_list(user_id: Optional[str]) -> List[str]:
    """ユーザーの苦手（回避）リストを取得する（スタブ）。

    引数:
        user_id: ユーザー識別子

    戻り値:
        氏名（またはID）の一覧

    TODO:
        - 登録・削除APIとの整合（双方向更新）
        - 上限数や重複の取り扱い
    """
    return ["佐藤", "鈴木"]
