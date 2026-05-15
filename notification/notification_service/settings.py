import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('NOTIFICATION_SECRET_KEY', 'notification-dev-secret')
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',
    'apps.notifications',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'notification_service.urls'
WSGI_APPLICATION = 'notification_service.wsgi.application'
ASGI_APPLICATION = 'notification_service.asgi.application'


def _database_config():
    database_url = os.getenv('DATABASE_URL', '').strip()
    if database_url:
        parsed = urlparse(database_url)
        if parsed.scheme in {'postgres', 'postgresql'}:
            return {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': parsed.path.lstrip('/'),
                'USER': parsed.username or '',
                'PASSWORD': parsed.password or '',
                'HOST': parsed.hostname or 'localhost',
                'PORT': str(parsed.port or 5432),
            }

    return {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'soccho'),
        'USER': os.getenv('POSTGRES_USER', 'soccho'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'soccho'),
        'HOST': os.getenv('POSTGRES_HOST', 'postgres'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
    }

DATABASES = {
    'default': _database_config()
}

REDIS_CACHE_URL = os.getenv('REDIS_CACHE_URL', 'redis://redis:6379/0')
CHANNEL_LAYERS_REDIS_URL = os.getenv('CHANNEL_LAYERS_REDIS_URL', 'redis://redis:6379/2')

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [CHANNEL_LAYERS_REDIS_URL],
        },
    },
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_SECRET_KEY = os.getenv('AUTH_SECRET_KEY', SECRET_KEY)
TRANSACTION_HTTP_BASE_URL = os.getenv(
    'TRANSACTION_HTTP_BASE_URL',
    'https://soccho-transaction.onrender.com',
)
