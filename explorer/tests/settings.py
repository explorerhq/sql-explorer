from test_project.settings import *  # noqa

EXPLORER_ENABLE_ANONYMOUS_STATS = False
EXPLORER_TASKS_ENABLED = False  # set to true to test async tasks
EXPLORER_AI_API_KEY = None  # set to any value to enable assistant
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
