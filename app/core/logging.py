import logging


def setup_logging(level: int = logging.INFO) -> None:
    """ロギングの基本設定を行う。

    引数:
        level: ログレベル（デフォルト INFO）

    備考:
    - 必要であれば JSON フォーマットに切り替え可能（例: python-json-logger）
    - ライブラリごとのレベル調整（uvicorn, httpx など）は別途設定
    - リクエストID付与などはミドルウェアで対応
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )

