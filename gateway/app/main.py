from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.middleware.cors import configure_cors
from app.middleware.jwt_validator import JWTValidationMiddleware
from app.routes.health import router as health_router
from app.routes.proxy import router as proxy_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title='Soccho Gateway', lifespan=lifespan)
app.add_middleware(JWTValidationMiddleware)
configure_cors(app)

app.include_router(health_router)
app.include_router(proxy_router)


@app.get('/healthz')
async def healthz():
    return {'status': 'ok'}
