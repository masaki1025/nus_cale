import logging


def setup_logging(level: int = logging.INFO) -> None:
    """ロギングの基本設定を行う。

    引数:
        level: ログレベル（デフォルト INFO）

    TODO:
    - 本番では JSON 形式の構造化ログに切替（例: `python-json-logger` 等）
    - モジュールごとのレベル調整（uvicorn, httpx などの冗長ログ低減）
    - リクエストIDの付与（ミドルウェア連携）
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
