import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin_service.settings')
os.environ.setdefault('DEBUG', 'false')
os.environ.setdefault('ADMIN_SECRET_KEY', 'ci-admin-secret')
# Production wiring only. Inject DATABASE_URL explicitly when running tests.
os.environ.setdefault('ADMIN_URL_PATH', '119115131318115/')
