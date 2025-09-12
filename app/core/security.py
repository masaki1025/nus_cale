from fastapi import Header, HTTPException, status

from app.core.config import get_settings


async def require_admin(x_admin_token: str = Header(default="", alias="X-Admin-Token")) -> None:
    """管理系エンドポイント用の簡易APIキー認証。

    - ヘッダ `X-Admin-Token` の値を `.env` の `ADMIN_API_KEY` と照合
    - 不一致/未設定の場合は 401 を返す
    """
    settings = get_settings()
    expected = settings.admin_api_key
    if not expected:
        # 運用上の安全のため、未設定なら拒否
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ADMIN_API_KEY が未設定です",
        )
    if not x_admin_token or x_admin_token != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無効な管理トークンです",
        )

