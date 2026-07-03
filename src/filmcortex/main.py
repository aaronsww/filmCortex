from contextlib import asynccontextmanager

from fastapi import FastAPI

from filmcortex.api.router import api_router
from filmcortex.config.settings import settings
from filmcortex.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    await engine.dispose()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.app_debug,
        lifespan=lifespan,
    )
    app.include_router(api_router, prefix="/api")
    return app


app = create_app()
