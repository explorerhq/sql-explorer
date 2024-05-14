from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured
from django.db import connections as djcs
from django.utils.translation import gettext_lazy as _


class ExplorerAppConfig(AppConfig):

    name = "explorer"
    verbose_name = _("SQL Explorer")
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        from explorer.schema import build_async_schemas
        _validate_connections()
        build_async_schemas()


def _get_default():
    from explorer.app_settings import EXPLORER_DEFAULT_CONNECTION
    return EXPLORER_DEFAULT_CONNECTION


def _get_explorer_connections():
    from explorer.app_settings import EXPLORER_CONNECTIONS
    return EXPLORER_CONNECTIONS


def _validate_connections():

    # Validate connections, when using settings.EXPLORER_CONNECTIONS
    # Skip if none are configured, as the app will use user-configured connections (DatabaseConnection models)
    if _get_explorer_connections().values() and _get_default() not in _get_explorer_connections().values():
        raise ImproperlyConfigured(
            f"EXPLORER_DEFAULT_CONNECTION is {_get_default()}, "
            f"but that alias is not present in the values of "
            f"EXPLORER_CONNECTIONS"
        )

    for name, conn_name in _get_explorer_connections().items():
        if conn_name not in djcs:
            raise ImproperlyConfigured(
                f"EXPLORER_CONNECTIONS contains ({name}, {conn_name}), "
                f"but {conn_name} is not a valid Django DB connection."
            )
