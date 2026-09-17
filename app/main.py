import logging
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api import health, json_api, web
from app.config import get_settings

logger = logging.getLogger("book_recommender")


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("application_started")
    yield
    logger.info("application_stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/api/docs" if settings.app_env != "production" else None,
        redoc_url=None,
    )

    application.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
    application.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        same_site="lax",
        https_only=settings.session_cookie_secure,
        max_age=60 * 60 * 24 * 7,
    )

    @application.middleware("http")
    async def request_context(request: Request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))[:128]
        started = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data:; style-src 'self'; "
            "script-src 'self'; connect-src 'self'; base-uri 'self'; form-action 'self'; "
            "frame-ancestors 'none'"
        )
        logger.info(
            "request_complete method=%s path=%s status=%s duration_ms=%.2f request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            (time.perf_counter() - started) * 1000,
            request_id,
        )
        return response

    @application.exception_handler(404)
    async def not_found(request: Request, _):
        if request.url.path.startswith("/api/"):
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        return web.templates.TemplateResponse(
            request=request,
            name="404.html",
            context={"request": request},
            status_code=404,
        )

    static_dir = Path(__file__).resolve().parent / "static"
    application.mount("/static", StaticFiles(directory=static_dir), name="static")
    application.include_router(health.router)
    application.include_router(json_api.router)
    application.include_router(web.router)
    return application


app = create_app()
