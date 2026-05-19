import logging

from django.apps import AppConfig
from django.db import connection
from django.db.utils import DatabaseError, OperationalError


logger = logging.getLogger(__name__)


def ensure_pg_trgm_extension() -> None:
    try:
        with connection.cursor() as cursor:
            cursor.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm;')
    except (OperationalError, DatabaseError) as exc:
        # Best-effort only: managed DB roles may not allow extension DDL.
        logger.warning('Could not ensure pg_trgm extension: %s', exc)


class SearchConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.search'

    def ready(self) -> None:
        ensure_pg_trgm_extension()
