import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "notification_service.settings")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("NOTIFICATION_SECRET_KEY", "ci-notification-secret")
os.environ.setdefault("AUTH_SECRET_KEY", "ci-auth-secret")
# Production wiring only. Inject DATABASE_URL / REDIS_CACHE_URL / CHANNEL_LAYERS_REDIS_URL explicitly when running tests.
