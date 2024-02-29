from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured
from django.db import connections as djcs
from django.db.utils import OperationalError
from django.utils.translation import gettext_lazy as _


class ExplorerAppConfig(AppConfig):

    name = "explorer"
    verbose_name = _("SQL Explorer")
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        from explorer.schema import build_async_schemas
        _validate_connections()
        build_async_schemas()
        track_summary_stats()


def _get_default():
    from explorer.app_settings import EXPLORER_DEFAULT_CONNECTION
    return EXPLORER_DEFAULT_CONNECTION


def _get_explorer_connections():
    from explorer.app_settings import EXPLORER_CONNECTIONS
    return EXPLORER_CONNECTIONS


def _validate_connections():

    # Validate connections
    if _get_default() not in _get_explorer_connections().values():
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


def track_summary_stats():
    from explorer.tracker import Stat, StatNames
    from explorer.tracker import gather_summary_stats
    from explorer.models import Query

    # Test to see if migrations have been applied.
    # If not, then we won't gather start-up stats (no need -- there's nothing interesting to report on)
    # We can't use a post_migrate hook because in many cases the app will be starting
    # and there won't be any migrations running! So the signal would never get called.
    # Django doesn't actually have a way of running code on application initialization,
    # so we are kinda faking it by doing this.
    try:
        Query.objects.first()
    except OperationalError:
        return
    else:
        payload = gather_summary_stats()
        Stat(StatNames.STARTUP_STATS, payload).track()
