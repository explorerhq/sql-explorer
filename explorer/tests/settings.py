from test_project.settings import *  # noqa

EXPLORER_ENABLE_ANONYMOUS_STATS = False
EXPLORER_TASKS_ENABLED = True
EXPLORER_AI_API_KEY = "foo"
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_TASK_ALWAYS_EAGER = True
TEST_MODE = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "tst1",
        "TEST": {
            "NAME": "tst1"
        }
    },
    "alt": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "tst2",
        "TEST": {
            "NAME": "tst2"
        }
    },
    "not_registered": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "tst3",
        "TEST": {
            "NAME": "tst3"
        }
    }
}

EXPLORER_CONNECTIONS = {
    "SQLite": "default",
    "Another": "alt",
}

class PrimaryDatabaseRouter:
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db == "default":
            return None
        return False

DATABASE_ROUTERS = ["explorer.tests.settings.PrimaryDatabaseRouter"]
