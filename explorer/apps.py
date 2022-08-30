from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured
from django.db import connections as djcs
from django.utils.translation import gettext_lazy as _


class ExplorerAppConfig(AppConfig):
    name = 'explorer'
    verbose_name = _('SQL Explorer')
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        from explorer.schema import build_async_schemas
        _validate_connections()
        build_async_schemas()


def _get_app_settings():
    from explorer import app_settings
    return app_settings


def _validate_connections():
    app_settings = _get_app_settings()

    # Validate connections
    if app_settings.EXPLORER_DEFAULT_CONNECTION not in app_settings.EXPLORER_CONNECTIONS.keys():
        if app_settings.EXPLORER_DEFAULT_CONNECTION in app_settings.EXPLORER_CONNECTIONS.values():
            # fix-up default for any setup still using the django DB name
            # rather than the alias name
            for k, v in app_settings.EXPLORER_CONNECTIONS.items():
                if v == app_settings.EXPLORER_DEFAULT_CONNECTION:
                    app_settings.EXPLORER_DEFAULT_CONNECTION = k
                    break
        else:
            raise ImproperlyConfigured(
                f'EXPLORER_DEFAULT_CONNECTION is {app_settings.EXPLORER_DEFAULT_CONNECTION}, '
                f'but that alias is not present in the values of EXPLORER_CONNECTIONS'
            )

    for name, conn_name in app_settings.EXPLORER_CONNECTIONS.items():
        if conn_name not in djcs:
            raise ImproperlyConfigured(
                f'EXPLORER_CONNECTIONS contains ({name}, {conn_name}), '
                f'but {conn_name} is not a valid Django DB connection.'
            )
