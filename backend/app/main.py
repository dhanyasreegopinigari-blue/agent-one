import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import health
from app.config import get_settings
from app.errors import AppError
from app.logging_setup import setup_logging

logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    settings = get_settings()

    # Ensure directories exist
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.sessions_dir.mkdir(parents=True, exist_ok=True)

    # Database initialization (wired in P2)
    try:
        from app.db.database import init_db
        from app.db.repository import fail_stale_documents

        init_db()
        fail_stale_documents()
    except (ImportError, AttributeError):
        pass
    except Exception as e:
        logger.error("Failed during DB init or stale doc cleanup: %s", e)

    # Warm models (wired in P6)
    try:
        import asyncio

        from app.llm.ollama_client import warm_models

        asyncio.create_task(warm_models())
    except (ImportError, AttributeError):
        pass
    except Exception as e:
        logger.warning("Failed to schedule model warmup: %s", e)

    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Agent One API",
        version="3.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_origin_regex=settings.cors_origin_regex,
        allow_methods=["*"],
        allow_headers=["Authorization", "Content-Type"],
        allow_credentials=False,
    )

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"error": {"code": "VALIDATION_ERROR", "message": str(exc)}},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled server exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "INTERNAL", "message": "An internal server error occurred."}},
        )

    app.include_router(health.router)

    return app


app = create_app()
