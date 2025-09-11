from fastapi import FastAPI

from app.endpoints import health, line, jobs, admin
from app.core.config import get_settings
from app.core.scheduler import setup_schedules, shutdown_schedules


def create_app() -> FastAPI:
    """FastAPI アプリケーションを生成し、各ルータを登録する。"""
    app = FastAPI(title="Nus Cale API")
    app.include_router(health.router)
    app.include_router(line.router)
    app.include_router(jobs.router)
    app.include_router(admin.router)

    # 起動時にスケジューラを設定
    @app.on_event("startup")
    async def _on_startup() -> None:
        settings = get_settings()
        try:
            setup_schedules(settings.notify_schedules)
        except Exception:
            import logging
            logging.getLogger("app.scheduler").exception("スケジューラ初期化に失敗しました")

    # 終了時にスケジューラを停止
    @app.on_event("shutdown")
    async def _on_shutdown() -> None:
        try:
            shutdown_schedules(wait=False)
        except Exception:
            pass

    return app


app = create_app()

