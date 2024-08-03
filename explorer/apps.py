from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
from django.db import transaction, DEFAULT_DB_ALIAS, connections


class ExplorerAppConfig(AppConfig):

    name = "explorer"
    verbose_name = _("SQL Explorer")
    default_auto_field = "django.db.models.AutoField"


# SQL Explorer DatabaseConnection models store connection info but are always translated into "django-style" connections
# before use, because we use Django's DB engine to run queries, gather schema information, etc.

# In general this isn't a problem; we cough up a django-style connection and all is well. The exception is when using
# the `with transaction.atomic(using=...):` context manager. The atomic() function takes a connection *alias* argument
# and the retrieves the connection from settings.DATABASES. But of course if we are providing a user-created connection
# alias, Django doesn't find it.

# The solution is to monkey-patch the `get_connection` function within transaction.atomic to make it aware of the
# user-created connections.

# This code should be double-checked against new versions of Django to make sure the original logic is still correct.

def new_get_connection(using=None):
    from explorer.ee.db_connections.models import DatabaseConnection
    if using is None:
        using = DEFAULT_DB_ALIAS
    if using in connections:
        return connections[using]
    return DatabaseConnection.objects.get(alias=using).as_django_connection()

transaction.get_connection = new_get_connection
