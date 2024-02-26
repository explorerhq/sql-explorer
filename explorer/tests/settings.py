from test_project.settings import *  # noqa

EXPLORER_ENABLE_ANONYMOUS_STATS = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "tst",
        "TEST": {
            "NAME": "tst"
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
