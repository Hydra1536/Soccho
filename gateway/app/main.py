import asyncio
import logging
from contextlib import asynccontextmanager, suppress

import httpx
from fastapi import FastAPI

from app.config import get_settings
from app.middleware.cors import configure_cors
from app.middleware.jwt_validator import JWTValidationMiddleware
from app.routes.health import router as health_router
from app.routes.proxy import router as proxy_router

logger = logging.getLogger(__name__)


async def _keepalive_loop():
    settings = get_settings()
    interval = max(60, int(settings.keepalive_interval_seconds or 600))
    targets = [
        ("gateway", "https://soccho-gateway.onrender.com/healthz"),
        ("social", f"{settings.social_http_base_url.rstrip('/')}/health/"),
        ("transaction", f"{settings.transaction_http_base_url.rstrip('/')}/health/"),
        ("notification", f"{settings.notification_http_base_url.rstrip('/')}/health/"),
    ]

    async with httpx.AsyncClient(timeout=15.0) as client:
        while True:
            for name, url in targets:
                try:
                    response = await client.get(url)
                    logger.info(
                        "Keepalive ping",
                        extra={
                            "target": name,
                            "url": url,
                            "status_code": response.status_code,
                        },
                    )
                except Exception as exc:
                    logger.warning(
                        "Keepalive ping failed target=%s error=%s", name, str(exc)
                    )
            await asyncio.sleep(interval)


@asynccontextmanager
async def lifespan(app: FastAPI):
    keepalive_task = asyncio.create_task(_keepalive_loop())
    try:
        yield
    finally:
        keepalive_task.cancel()
        with suppress(asyncio.CancelledError):
            await keepalive_task


app = FastAPI(title="Soccho Gateway", lifespan=lifespan)
app.add_middleware(JWTValidationMiddleware)
configure_cors(app)

app.include_router(health_router)
app.include_router(proxy_router)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
