from fastapi import FastAPI

from app.endpoints import health, line, jobs, admin


def create_app() -> FastAPI:
    """FastAPI アプリケーションを生成し、各ルータを登録する。

    TODO:
    - CORS やミドルウェア（ロギング、例外ハンドラ）の追加
    - 起動時/終了時イベントでのリソース初期化・解放
    """
    app = FastAPI(title="Nus Cale API")
    app.include_router(health.router)
    app.include_router(line.router)
    app.include_router(jobs.router)
    app.include_router(admin.router)
    return app


app = create_app()
