import os
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from explorer.ee.db_connections.utils import uploaded_db_local_path, quick_hash

from django_cryptography.fields import encrypt


class DatabaseConnection(models.Model):

    SQLITE = "django.db.backends.sqlite3"

    DATABASE_ENGINES = (
        (SQLITE, "SQLite3"),
        ("django.db.backends.postgresql", "PostgreSQL"),
        ("django.db.backends.mysql", "MySQL"),
        ("django.db.backends.oracle", "Oracle"),
        ("django.db.backends.mysql", "MariaDB"),
        ("django_cockroachdb", "CockroachDB"),
        ("mssql", "SQL Server (mssql-django)"),
        ("django_snowflake", "Snowflake"),
    )

    alias = models.CharField(max_length=255, unique=True)
    engine = models.CharField(max_length=255, choices=DATABASE_ENGINES)
    name = models.CharField(max_length=255)
    user = encrypt(models.CharField(max_length=255, blank=True, null=True))
    password = encrypt(models.CharField(max_length=255, blank=True, null=True))
    host = encrypt(models.CharField(max_length=255, blank=True))
    port = models.CharField(max_length=255, blank=True)
    extras = models.JSONField(blank=True, null=True)
    upload_fingerprint = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.alias})"

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

    def download_sqlite_if_needed(self):
        download = not os.path.exists(self.local_name) or self.local_fingerprint() != self.upload_fingerprint

        if download:
            self._download_sqlite()
            self.update_fingerprint()


    @property
    def is_upload(self):
        return self.engine == self.SQLITE and self.host

    @property
    def local_name(self):
        if self.is_upload:
            return uploaded_db_local_path(self.name)

    def delete_local_sqlite(self):
        if self.is_upload and os.path.exists(self.local_name):
            os.remove(self.local_name)

    @classmethod
    def from_django_connection(cls, connection_alias):
        conn = settings.DATABASES.get(connection_alias)
        if conn:
            return DatabaseConnection(
                alias=connection_alias,
                engine=conn.get("ENGINE"),
                name=conn.get("NAME"),
                user=conn.get("USER"),
                password=conn.get("PASSWORD"),
                host=conn.get("HOST"),
                port=conn.get("PORT"),
            )


@receiver(pre_save, sender=DatabaseConnection)
def validate_database_connection(sender, instance, **kwargs):
    if instance.name in settings.DATABASES.keys():
        raise ValidationError(f"Database name '{instance.name}' already exists.")
