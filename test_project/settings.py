import django
import os
import djcelery
SECRET_KEY = 'shhh'
DEBUG = True
STATIC_URL = '/static/'

ALLOWED_HOSTS = ['0.0.0.0', 'localhost', '127.0.0.1']

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'tmp',
        'TEST': {
            'NAME': 'tmp'
        }
    },
    'alt': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'tmp2',
        'TEST': {
            'NAME': 'tmp2'
        }
    },
    'not_registered': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'tmp3',
        'TEST': {
            'NAME': 'tmp3'
        }
    }
}

EXPLORER_CONNECTIONS = {
    #'Postgres': 'postgres',
    #'MySQL': 'mysql',
    'SQLite': 'default',
    'Another': 'alt'
}
EXPLORER_DEFAULT_CONNECTION = 'default'

ROOT_URLCONF = 'explorer.tests.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.static',
                'django.template.context_processors.request',
            ],
            'debug': DEBUG
        },
    },
]

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'explorer',
    'djcelery'
)

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
)

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

TEST_RUNNER = 'djcelery.contrib.test_runner.CeleryTestSuiteRunner'

djcelery.setup_loader()
CELERY_ALWAYS_EAGER = True
BROKER_BACKEND = 'memory'

# Explorer-specific

EXPLORER_TRANSFORMS = (
    ('foo', '<a href="{0}">{0}</a>'),
    ('bar', 'x: {0}')
)

EXPLORER_USER_QUERY_VIEWS = {}
EXPLORER_TASKS_ENABLED = True
EXPLORER_S3_BUCKET = 'thisismybucket.therearemanylikeit.butthisoneismine'
