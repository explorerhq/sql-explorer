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

    # Django doesn't actually have a way of running code on application initialization, so we have come up with this.
    # The app.ready() method (the call site for this function) is invoked *before* any migrations are run. So if were
    # to just call this function in ready(), without the try: block, then it would always fail the very first time
    # Django runs (and e.g. in test runs) because no tables have yet been created. The intuitive way to handle this with
    # Django would be to tie into the post_migrate signal in ready() and run this function on post_migrate. But that
    # doesn't work because that signal is only called if indeed a migrations has been applied. If the app restarts and
    # there are no new migrations, the signal never fires. So instead we check if the Query table exists, and if it
    # does, we're good to gather stats.
    try:
        Query.objects.first()
    except OperationalError:
        return
    else:
        payload = gather_summary_stats()
        Stat(StatNames.STARTUP_STATS, payload).track()
