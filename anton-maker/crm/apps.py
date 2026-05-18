# CRM Application Configuration

from django.apps import AppConfig
from django.db.backends.signals import connection_created
from django.conf import settings


class CrmConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'crm'
    verbose_name = 'Управление производством'

    def ready(self):
        # Apply SQLite PRAGMAs for WAL mode on each connection
        if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
            connection_created.connect(apply_sqlite_pragmas, sender=self)


def apply_sqlite_pragmas(sender, connection, **kwargs):
    """Apply SQLite PRAGMA settings for optimal performance."""
    if hasattr(settings, 'SQLITE_PRAGMAS'):
        cursor = connection.cursor()
        for pragma in settings.SQLITE_PRAGMAS:
            try:
                cursor.execute(pragma)
            except Exception:
                pass  # Ignore errors if PRAGMA not supported
