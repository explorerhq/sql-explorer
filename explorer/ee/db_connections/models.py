import os
import json
import logging
from django.core.exceptions import ImproperlyConfigured
from django.db import models, DatabaseError, connections, transaction
from django.db.utils import load_backend
from explorer.app_settings import EXPLORER_CONNECTIONS
from explorer.ee.db_connections.utils import quick_hash, uploaded_db_local_path
from django.core.cache import cache
from django_cryptography.fields import encrypt

logger = logging.getLogger(__name__)

# The package that provides each engine's driver, so error messages can say what to install
DRIVER_PACKAGES = {
    "django.db.backends.postgresql": "psycopg",
    "django.db.backends.mysql": "mysqlclient",
    "django.db.backends.oracle": "oracledb",
    "django_cockroachdb": "django-cockroachdb",
    "mssql": "mssql-django",
    "django_snowflake": "django-snowflake",
}


class DatabaseConnectionManager(models.Manager):

    def uploads(self):
        return self.filter(engine=DatabaseConnection.SQLITE, host__isnull=False)

    def non_uploads(self):
        return self.exclude(engine=DatabaseConnection.SQLITE, host__isnull=False)

    def default(self):
        return self.filter(default=True).first()


class DatabaseConnection(models.Model):

    objects = DatabaseConnectionManager()

    SQLITE = "django.db.backends.sqlite3"
    DJANGO = "django_connection"

    DATABASE_ENGINES = (
        (SQLITE, "SQLite3"),
        ("django.db.backends.postgresql", "PostgreSQL"),
        ("django.db.backends.mysql", "MySQL"),
        ("django.db.backends.oracle", "Oracle"),
        ("django.db.backends.mysql", "MariaDB"),
        ("django_cockroachdb", "CockroachDB"),
        ("mssql", "SQL Server (mssql-django)"),
        ("django_snowflake", "Snowflake"),
        (DJANGO, "Django Connection"),
    )

    alias = models.CharField(max_length=255, unique=True)
    engine = models.CharField(max_length=255, choices=DATABASE_ENGINES)
    name = models.CharField(max_length=255, blank=True, null=True)
    user = encrypt(models.CharField(max_length=255, blank=True, null=True))
    password = encrypt(models.CharField(max_length=255, blank=True, null=True))
    host = encrypt(models.CharField(max_length=255, blank=True))
    port = models.CharField(max_length=255, blank=True, null=True)
    extras = models.JSONField(blank=True, null=True)
    upload_fingerprint = models.CharField(max_length=255, blank=True, null=True)
    default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.alias}"

    def update_fingerprint(self):
        self.upload_fingerprint = self.local_fingerprint()
        self.save()

    def local_fingerprint(self):
        if os.path.exists(self.local_name):
            return quick_hash(self.local_name)

    def _download_sqlite(self):
        from explorer.utils import get_s3_bucket
        s3 = get_s3_bucket()
        s3.download_file(self.host, self.local_name)

    def _download_needed(self):
        # If the file doesn't exist, obviously we need to download it
        # If it does exist, then check if it's out of date. But only check if in fact the DatabaseConnection has been
        # saved to the DB. For example, we might be validating an unsaved connection, in which case the fingerprint
        # won't be set yet.
        return (not os.path.exists(self.local_name) or
               (self.id is not None and self.local_fingerprint() != self.upload_fingerprint))

    def download_sqlite_if_needed(self):

        if self._download_needed():
            cache_key = f"download_lock_{self.local_name}"
            lock_acquired = cache.add(cache_key, "locked", timeout=300)  # Timeout after 5 minutes

            if lock_acquired:
                try:
                    if self._download_needed():
                        self._download_sqlite()
                        self.update_fingerprint()
                finally:
                    cache.delete(cache_key)

    @classmethod
    def missing_driver_message(cls, engine):
        """Returns an explanation if the driver for this engine can't be loaded, or None if it can."""
        if not engine or engine == cls.DJANGO:
            return None
        try:
            load_backend(engine)
        except ImproperlyConfigured as e:
            logger.info(f"Database driver for {engine} could not be loaded: {e}")
            return cls._driver_error_message(engine)
        return None

    @classmethod
    def _driver_error_message(cls, engine):
        label = " / ".join(name for value, name in cls.DATABASE_ENGINES if value == engine) or engine
        package = DRIVER_PACKAGES.get(engine)
        install = f" Install the '{package}' package on the server to use it." if package else ""
        return f"The database driver for {label} isn't installed.{install}"

    @property
    def is_upload(self):
        return self.engine == self.SQLITE and self.host

    @property
    def is_django_alias(self):
        return self.engine == DatabaseConnection.DJANGO

    @property
    def local_name(self):
        if self.is_upload:
            return uploaded_db_local_path(self.name)

    def delete_local_sqlite(self):
        if self.is_upload and os.path.exists(self.local_name):
            os.remove(self.local_name)

    # See the comment in apps.py for a more in-depth explanation of what's going on here.
    def as_django_connection(self):
        if self.is_upload:
            self.download_sqlite_if_needed()

        # You can't access a Django-backed connection unless it has been registered in EXPLORER_CONNECTIONS.
        # Otherwise, users with userspace DatabaseConnection rights could connect to underlying Django DB connections.
        if self.is_django_alias:
            if self.alias in EXPLORER_CONNECTIONS.values():
                return connections[self.alias]
            else:
                raise DatabaseError("Django alias connections must be registered in EXPLORER_CONNECTIONS.")

        connection_settings = {
            "ENGINE": self.engine,
            "NAME": self.name if not self.is_upload else self.local_name,
            "USER": self.user,
            "PASSWORD": self.password,
            "HOST": self.host if not self.is_upload else None,
            "PORT": self.port,
            "TIME_ZONE": None,
            "CONN_MAX_AGE": 0,
            "CONN_HEALTH_CHECKS": False,
            "OPTIONS": {},
            "TEST": {},
            "AUTOCOMMIT": True,
            "ATOMIC_REQUESTS": False,
        }

        if self.extras:
            extras_dict = json.loads(self.extras) if isinstance(self.extras, str) else self.extras
            connection_settings.update(extras_dict)

        try:
            backend = load_backend(self.engine)
            return backend.DatabaseWrapper(connection_settings, self.alias)
        except ImproperlyConfigured as e:
            # load_backend raises this when the engine's driver isn't installed
            raise DatabaseError(self._driver_error_message(self.engine)) from e
        except DatabaseError as e:
            raise DatabaseError(f"Failed to create explorer connection: {e}") from e

    def save(self, *args, **kwargs):
        # If this instance is marked as default, unset the default on all other instances
        if self.default:
            with transaction.atomic():
                DatabaseConnection.objects.filter(default=True).update(default=False)
        else:
            # If there is no default set yet, make this newly created one the default.
            has_default = DatabaseConnection.objects.filter(default=True).exists()
            if not has_default:
                self.default = True

        super().save(*args, **kwargs)
