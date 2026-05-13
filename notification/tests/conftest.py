import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notification_service.settings')
os.environ.setdefault('DEBUG', 'false')
os.environ.setdefault('NOTIFICATION_SECRET_KEY', 'ci-notification-secret')
os.environ.setdefault('AUTH_SECRET_KEY', 'ci-auth-secret')
os.environ.setdefault('DATABASE_URL', 'postgresql://soccho:soccho@localhost:5432/soccho')
os.environ.setdefault('REDIS_CACHE_URL', 'redis://localhost:6379/0')
os.environ.setdefault('CHANNEL_LAYERS_REDIS_URL', 'redis://localhost:6379/2')


@pytest.fixture(autouse=True)
def mock_grpc(monkeypatch):
    try:
        import grpc
    except Exception:
        return

    class DummyChannel:
        async def close(self):
            return None

        def unary_unary(self, *_args, **_kwargs):
            async def _call(_request=None):
                return {'ok': True}

            return _call

    monkeypatch.setattr(grpc.aio, 'insecure_channel', lambda *_a, **_k: DummyChannel())
