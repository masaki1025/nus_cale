from pydantic import BaseModel


class HealthResponse(BaseModel):
    """/healthz のレスポンスモデル（拡張余地あり）。

    TODO:
    - バージョンやビルド情報、依存サービスの状態などを追加
    """
    status: str = "ok"
