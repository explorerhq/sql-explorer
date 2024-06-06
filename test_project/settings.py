import os


SECRET_KEY = "shhh"
DEBUG = True
STATIC_URL = "/static/"
VITE_DEV_MODE = False

ALLOWED_HOSTS = ["0.0.0.0", "localhost", "127.0.0.1"]

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "tmp",
        "TEST": {
            "NAME": "tmp"
        }
    },
    "alt": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "tmp2",
        "TEST": {
            "NAME": "tmp2"
        }
    },
}

EXPLORER_CONNECTIONS = {
    "SQLite": "default",
    "Another": "alt",
}
EXPLORER_DEFAULT_CONNECTION = "default"

ROOT_URLCONF = "test_project.urls"

PROJECT_PATH = os.path.realpath(os.path.dirname(__file__))

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.static",
                "django.template.context_processors.request",
            ],
            "debug": DEBUG
        },
    },
]

INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",
    "explorer",
)

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
)

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

# added to help debug tasks
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Explorer-specific

EXPLORER_TRANSFORMS = (
    ("foo", '<a href="{0}">{0}</a>'),
    ("bar", "x: {0}")
)

EXPLORER_USER_QUERY_VIEWS = {}

# Tasks disabled by default, but if you have celery installed
# make sure the broker URL is set correctly
EXPLORER_TASKS_ENABLED = False
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL')

EXPLORER_S3_BUCKET = os.environ.get("EXPLORER_S3_BUCKET")
EXPLORER_S3_ACCESS_KEY = os.environ.get("EXPLORER_S3_ACCESS_KEY")
EXPLORER_S3_SECRET_KEY = os.environ.get("EXPLORER_S3_SECRET_KEY")
EXPLORER_AI_API_KEY = os.environ.get("AI_API_KEY")
EXPLORER_ASSISTANT_BASE_URL = os.environ.get("AI_BASE_URL")
EXPLORER_DB_CONNECTIONS_ENABLED = True
