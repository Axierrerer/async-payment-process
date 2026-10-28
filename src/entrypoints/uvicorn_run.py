from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import Depends, FastAPI
from fastapi.exceptions import RequestValidationError
from sqlalchemy.ext.asyncio import AsyncEngine

from core.base_errors import BaseAppError
from core.container import get_container
from core.settings import AllSettings
from transport.api.v1.depends import verify_api_key
from transport.api.v1.errors import (
    app_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from transport.api.v1.routers import v1_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    yield
    db_engine = get_container().resolve(AsyncEngine)
    await db_engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.include_router(v1_router, prefix="/api/v1", dependencies=[Depends(verify_api_key)])
    app.add_exception_handler(BaseAppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
    return app


async def main() -> None:
    settings = get_container().resolve(AllSettings)
    config = uvicorn.Config(
        app=create_app(),
        host=settings.app.HOST,
        port=settings.app.PORT,
        proxy_headers=True,
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
