import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'social_service.settings')
os.environ.setdefault('DEBUG', 'false')
os.environ.setdefault('SOCIAL_SECRET_KEY', 'ci-social-secret')
os.environ.setdefault('DATABASE_URL', 'postgresql://soccho:soccho@localhost:5432/soccho')
os.environ.setdefault('REDIS_CACHE_URL', 'redis://localhost:6379/0')
