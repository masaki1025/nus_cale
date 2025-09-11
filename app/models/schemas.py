from pydantic import BaseModel


class HealthResponse(BaseModel):
    """/healthz のレスポンスモデル（今後拡張予定）。"""
    status: str = "ok"
