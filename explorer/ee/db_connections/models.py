import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from explorer.ee.db_connections.utils import user_dbs_local_dir

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
        ("django.db.backends.sqlserver", "SQL Server (mssql-django)"),
    )

    alias = models.CharField(max_length=255, unique=True)
    engine = models.CharField(max_length=255, choices=DATABASE_ENGINES)
    name = models.CharField(max_length=255)
    user = encrypt(models.CharField(max_length=255, blank=True))
    password = encrypt(models.CharField(max_length=255, blank=True))
    host = encrypt(models.CharField(max_length=255, blank=True))
    port = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.name} ({self.alias})"

    @property
    def is_upload(self):
        return self.engine == self.SQLITE and self.host

    @property
    def local_name(self):
        if self.is_upload:
            return os.path.join(user_dbs_local_dir(), self.name)

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
