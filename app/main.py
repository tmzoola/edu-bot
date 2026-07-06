import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from admin import setup_admin
from api.v1.admin_tools import router as admin_tools_router
from api.v1.webapp import api as webapp_api
from api.v1.webapp import pages as webapp_pages
from core.config import settings
from core.error_handlers import (
    app_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from core.exceptions import AppException
from db.session import session_factory
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from logging_config import setup_logging
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    setup_admin(app)

    # Start Telegram bot polling
    from bot.setup import bot, dp

    polling_task = asyncio.create_task(dp.start_polling(bot, skip_updates=True))
    logger.info("✅ Bot polling started")

    yield

    # Graceful shutdown
    logger.info("🔴 Shutting down...")
    polling_task.cancel()
    try:
        await polling_task
    except asyncio.CancelledError:
        pass
    await bot.session.close()
    logger.info("Bot stopped.")


app = FastAPI(
    title="Malaka",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url=None,
    version="1.0.0",
    lifespan=lifespan,
)

# Exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS.split(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)


@app.middleware("http")
async def https_proxy_middleware(request: Request, call_next):
    """
    Behind a TLS-terminating reverse proxy the app receives plain HTTP, so
    url_for()/redirects (e.g. starlette-admin's static assets and the login
    form action) come out as http:// and get blocked as mixed content on an
    https page. When the proxy signals https via X-Forwarded-Proto, rewrite the
    request scheme (and host) to https so all generated URLs are https, and add
    `upgrade-insecure-requests` as a browser-side safety net.
    """
    forwarded_proto = request.headers.get("x-forwarded-proto")

    if forwarded_proto == "https":
        scope = dict(request.scope)
        scope["scheme"] = "https"
        forwarded_host = request.headers.get("x-forwarded-host")
        if forwarded_host:
            scope["headers"] = [
                (b"host", forwarded_host.encode()),
                *[(k, v) for k, v in request.scope["headers"] if k != b"host"],
            ]
        request = Request(scope, request.receive)

    response = await call_next(request)

    if forwarded_proto == "https" or request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers.setdefault("Content-Security-Policy", "upgrade-insecure-requests")

    return response


# Routes
app.include_router(webapp_pages)
app.include_router(webapp_api)
app.include_router(admin_tools_router)


@app.get("/health")
async def health_check():
    try:
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"DB error: {e}")
        return JSONResponse(status_code=503, content={"status": "db-unreachable"})
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=True,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
