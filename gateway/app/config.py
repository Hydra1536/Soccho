from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    debug: bool = Field(default=False, alias='DEBUG')
    database_url: str = Field(default='', alias='DATABASE_URL')
    render_internal_redis_url: str = Field(default='redis://redis:6379', alias='RENDER_INTERNAL_REDIS_URL')
    redis_cache_url: str = Field(default='redis://redis:6379/0', alias='REDIS_CACHE_URL')
    celery_broker_url: str = Field(default='redis://redis:6379/1', alias='CELERY_BROKER_URL')
    celery_result_backend: str = Field(default='redis://redis:6379/1', alias='CELERY_RESULT_BACKEND')
    channel_layers_redis_url: str = Field(default='redis://redis:6379/2', alias='CHANNEL_LAYERS_REDIS_URL')
    aes_secret_key: str = Field(default='replace_me', alias='AES_SECRET_KEY')

    auth_secret_key: str = Field(default='replace_me', alias='AUTH_SECRET_KEY')
    social_secret_key: str = Field(default='replace_me', alias='SOCIAL_SECRET_KEY')
    transaction_secret_key: str = Field(default='replace_me', alias='TRANSACTION_SECRET_KEY')
    notification_secret_key: str = Field(default='replace_me', alias='NOTIFICATION_SECRET_KEY')
    admin_secret_key: str = Field(default='replace_me', alias='ADMIN_SECRET_KEY')
    gateway_secret_key: str = Field(default='replace_me', alias='GATEWAY_SECRET_KEY')

    auth_grpc_host: str = Field(default='auth', alias='AUTH_GRPC_HOST')
    auth_grpc_port: int = Field(default=8001, alias='AUTH_GRPC_PORT')
    auth_http_base_url: str = Field(default='https://soccho-auth.onrender.com', alias='AUTH_HTTP_BASE_URL')
    social_grpc_host: str = Field(default='social', alias='SOCIAL_GRPC_HOST')
    social_grpc_port: int = Field(default=8002, alias='SOCIAL_GRPC_PORT')
    social_http_base_url: str = Field(default='https://soccho-social.onrender.com', alias='SOCIAL_HTTP_BASE_URL')
    transaction_grpc_host: str = Field(default='transaction', alias='TRANSACTION_GRPC_HOST')
    transaction_grpc_port: int = Field(default=8003, alias='TRANSACTION_GRPC_PORT')
    transaction_http_base_url: str = Field(default='https://soccho-transaction.onrender.com', alias='TRANSACTION_HTTP_BASE_URL')
    notification_grpc_host: str = Field(default='notification', alias='NOTIFICATION_GRPC_HOST')
    notification_grpc_port: int = Field(default=8004, alias='NOTIFICATION_GRPC_PORT')
    notification_http_base_url: str = Field(default='https://soccho-notification.onrender.com', alias='NOTIFICATION_HTTP_BASE_URL')

    allowed_origins_raw: str = Field(default='https://soccho.onrender.com,https://soccho.vercel.app', alias='ALLOWED_ORIGINS')
    admin_url_path: str = Field(default='/admin', alias='ADMIN_URL_PATH')

    @property
    def allowed_origins(self) -> List[str]:
        required_origin = 'https://soccho.onrender.com'
        origins = [origin.strip() for origin in self.allowed_origins_raw.split(',') if origin.strip()]
        if required_origin not in origins:
            origins.append(required_origin)
        return origins


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
