import os

from celery import Celery
from celery.schedules import crontab


# Set the default Django settings module for the "celery" program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_project.settings")

app = Celery("test_project")

# Using a string here means the worker doesn"t have to serialize
# the configuration object to child processes.
# - namespace="CELERY" means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "explorer.tasks.snapshot_queries": {
        "task": "explorer.tasks.snapshot_queries",
        "schedule": crontab(hour="1", minute="0")
    },
    "explorer.tasks.truncate_querylogs": {
           "task": "explorer.tasks.truncate_querylogs",
           "schedule": crontab(hour="1", minute="10"),
           "kwargs": {"days": 30}
    },
    "explorer.tasks.remove_unused_sqlite_dbs": {
        "task": "explorer.tasks.remove_unused_sqlite_dbs",
        "schedule": crontab(hour="1", minute="20")
    },
    "explorer.tasks.build_async_schemas": {
        "task": "explorer.tasks.build_async_schemas",
        "schedule": crontab(hour="1", minute="30")
    }
}
