# Anonymous usage stats
# Opt-out by setting EXPLORER_ENABLE_ANONYMOUS_STATS = False in settings

from explorer import app_settings
import time
import requests
import json
import threading
from enum import Enum, auto
from django.core.cache import cache


def _instance_identifier():
    """
    We need a way of identifying unique instances of explorer to track usage.
    There isn't an established approach I'm aware of, so have come up with
    this. We take the timestamp of the first applied migration, and hash it
    with the secret key.
    """

    import hashlib
    from django.db.migrations.recorder import MigrationRecorder
    from django.conf import settings
    migration = MigrationRecorder.Migration.objects.all().order_by('applied').first()
    ts = migration.applied.timestamp()
    ts_bytes = str(ts).encode('utf-8')
    s_bytes = settings.SECRET_KEY.encode('utf-8')
    hashed_value = hashlib.sha256(ts_bytes + s_bytes).hexdigest()

    return hashed_value


def instance_identifier():
    key = "explorer_instance_identifier"
    r = cache.get(key)
    if not r:
        r = _instance_identifier()
        cache.set(key, r, 60 * 60 * 24)
    return r


class SelfNamedEnum(Enum):

    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        return name


class StatNames(SelfNamedEnum):

    QUERY_RUN = auto()
    STARTUP_STATS = auto()


class Stat(object):

    def __init__(self, name: StatNames, value):
        self.instanceId = instance_identifier()
        self.time = time.time()
        self.value = value
        self.name = name.value

    def track(self):
        if app_settings.EXPLORER_ENABLE_ANONYMOUS_STATS:
            data = json.dumps(self.__dict__)

            def _send():
                requests.post(app_settings.EXPLORER_COLLECT_ENDPOINT_URL(),
                              data=data,
                              headers={'Content-Type': 'application/json'})

            thread = threading.Thread(target=_send)
            thread.start()


def gather_summary_stats():
    from explorer.models import Query, QueryLog
    from django.db import connection
    from django.db.models import Count
    from django.db.migrations.recorder import MigrationRecorder
    from django.conf import settings

    ql_stats = QueryLog.objects.aggregate(
        total_count=Count('*'),
        unique_run_by_user_count=Count('run_by_user_id', distinct=True)
    )

    q_stats = Query.objects.aggregate(
        total_count=Count('*'),
        unique_connection_count=Count('connection', distinct=True)
    )

    return {
        "total_log_count": ql_stats['total_count'],
        "unique_run_by_user_count": ql_stats['unique_run_by_user_count'],
        "total_query_count": q_stats['total_count'],
        "unique_connection_count": q_stats['unique_connection_count'],
        "default_database": connection.vendor,
        "django_install_date":
            MigrationRecorder.Migration.objects.all().order_by('applied').first().applied.timestamp(),
        "debug": settings.DEBUG,
        "tasks_enabled": app_settings.ENABLE_TASKS,
    }
