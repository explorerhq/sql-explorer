# Anonymous usage stats
# Opt-out by setting EXPLORER_ENABLE_ANONYMOUS_STATS = False in settings

import logging
import time
import requests
import json
import threading
from enum import Enum, auto
from django.core.cache import cache
from django.db import connection
from django.db.models import Count
from django.db.migrations.recorder import MigrationRecorder
from django.conf import settings

logger = logging.getLogger(__name__)


def instance_identifier():
    from explorer.models import ExplorerValue
    key = "explorer_instance_uuid"
    r = cache.get(key)
    if not r:
        r = ExplorerValue.objects.get_uuid()
        cache.set(key, r, 60 * 60 * 24)
    return r


class SelfNamedEnum(Enum):

    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        return name


class StatNames(SelfNamedEnum):

    QUERY_RUN = auto()
    QUERY_STREAM = auto()
    STARTUP_STATS = auto()
    ASSISTANT_RUN = auto()


class Stat:

    STAT_COLLECTION_INTERVAL = 60 * 10  # Ten minutes
    STARTUP_STAT_COLLECTION_INTERVAL = 60 * 60 * 24 * 7  # A week

    def __init__(self, name: StatNames, value):
        self.instanceId = instance_identifier()
        self.time = time.time()
        self.value = value
        self.name = name.value

    @property
    def is_summary(self):
        return self.name == StatNames.STARTUP_STATS.value

    def should_send_summary_stats(self):
        from explorer.models import ExplorerValue
        last_send = ExplorerValue.objects.get_startup_last_send()
        if not last_send:
            return True
        else:
            return self.time - last_send >= self.STARTUP_STAT_COLLECTION_INTERVAL

    def send_summary_stats(self):
        from explorer.models import ExplorerValue
        payload = _gather_summary_stats()
        Stat(StatNames.STARTUP_STATS, payload).track()
        ExplorerValue.objects.set_startup_last_send(self.time)

    def track(self):
        from explorer import app_settings

        if not app_settings.EXPLORER_ENABLE_ANONYMOUS_STATS:
            return

        cache_key = "last_stat_sent_time"
        last_sent_time = cache.get(cache_key, 0)
        # Summary stats are tracked with a different time interval
        if self.is_summary or self.time - last_sent_time >= self.STAT_COLLECTION_INTERVAL:
            data = json.dumps(self.__dict__)
            thread = threading.Thread(target=_send, args=(data,))
            thread.start()
            cache.set(cache_key, self.time)

        # Every time we send any tracking, see if we have recently sent overall summary stats
        # Of course, sending the summary stats calls .track(), so we need to NOT call track()
        # again if we are in fact already in the process of sending summary stats. Otherwise,
        # we will end up in infinite recursion of track() calls.
        if not self.is_summary and self.should_send_summary_stats():
            self.send_summary_stats()


def _send(data):
    from explorer import app_settings
    try:
        requests.post(app_settings.EXPLORER_COLLECT_ENDPOINT_URL,
                      data=data,
                      headers={"Content-Type": "application/json"})
    except Exception as e:
        logger.warning(f"Failed to send stats: {e}")


def _get_install_quarter():
    first_migration = MigrationRecorder.Migration.objects. \
        filter(app="explorer").order_by("applied").first()

    if first_migration is not None:
        quarter = (first_migration.applied.month - 1) // 3 + 1  # Calculate the quarter
        year = first_migration.applied.year
        quarter_str = f"Q{quarter}-{year}"
    else:
        quarter_str = None
    return quarter_str


def _gather_summary_stats():

    from explorer import app_settings
    from explorer.models import Query, QueryLog
    from explorer.ee.db_connections.models import DatabaseConnection
    import explorer

    try:
        ql_stats = QueryLog.objects.aggregate(
            total_count=Count("*"),
            unique_run_by_user_count=Count("run_by_user_id", distinct=True)
        )

        q_stats = Query.objects.aggregate(
            total_count=Count("*"),
            unique_connection_count=Count("connection", distinct=True)
        )

        # Round the counts to provide additional anonymity
        return {
            "total_log_count": round(ql_stats["total_count"] * 0.1) * 10,
            "unique_run_by_user_count": round(ql_stats["unique_run_by_user_count"] * 0.2) * 5,
            "total_query_count": round(q_stats["total_count"] * 0.1) * 10,
            "unique_connection_count": round(q_stats["unique_connection_count"] * 0.2) * 5,
            "default_database": connection.vendor,
            "explorer_install_quarter": _get_install_quarter(),
            "debug": settings.DEBUG,
            "tasks_enabled": app_settings.ENABLE_TASKS,
            "unsafe_rendering": app_settings.UNSAFE_RENDERING,
            "transform_count": len(app_settings.EXPLORER_TRANSFORMS),
            "assistant_enabled": app_settings.has_assistant(),
            "user_dbs": DatabaseConnection.objects.count(),
            "version": explorer.get_version(),
            "charts_enabled": app_settings.EXPLORER_CHARTS_ENABLED
        }
    except Exception as e:
        return {"error": f"error gathering stats: {e}"}
