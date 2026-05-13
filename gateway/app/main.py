from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.grpc_client.auth_client import auth_client
from app.grpc_client.notification_client import notification_client
from app.grpc_client.social_client import social_client
from app.grpc_client.transaction_client import transaction_client
from app.middleware.cors import configure_cors
from app.middleware.jwt_validator import JWTValidationMiddleware
from app.routes.health import router as health_router
from app.routes.proxy import router as proxy_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await auth_client.connect()
    await social_client.connect()
    await transaction_client.connect()
    await notification_client.connect()
    try:
        yield
    finally:
        await auth_client.close()
        await social_client.close()
        await transaction_client.close()
        await notification_client.close()


app = FastAPI(title='Soccho Gateway', lifespan=lifespan)
configure_cors(app)
app.add_middleware(JWTValidationMiddleware)

app.include_router(health_router)
app.include_router(proxy_router)


@app.get('/healthz')
async def healthz():
    return {'status': 'ok'}
