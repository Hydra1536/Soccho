import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "transaction_service.settings")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("TRANSACTION_SECRET_KEY", "ci-transaction-secret")
# Production wiring only. Inject DATABASE_URL / REDIS_CACHE_URL / CELERY_BROKER_URL explicitly when running tests.
