import djcelery
SECRET_KEY = 'shhh'
SITE_ID = 1

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

ROOT_URLCONF = 'explorer.tests.urls'

EXPLORER_TRANSFORMS = (
    ('foo', '<a href="{0}">{0}</a>'),
    ('bar', 'x: {0}')
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.static",
    "django.core.context_processors.request",
)

TEMPLATE_LOADERS = (
    'django.template.loaders.app_directories.Loader',
    'django.template.loaders.filesystem.Loader',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'explorer',
    'djcelery'
)

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
)

STATIC_URL = '/static/'

MIDDLEWARE_CLASSES = ('django.contrib.sessions.middleware.SessionMiddleware',
                      'django.contrib.auth.middleware.AuthenticationMiddleware')

EXPLORER_USER_QUERY_VIEWS = {}

TEST_RUNNER = 'djcelery.contrib.test_runner.CeleryTestSuiteRunner'
djcelery.setup_loader()
EXPLORER_TASKS_ENABLED = True
CELERY_ALWAYS_EAGER = True
BROKER_BACKEND = 'memory'
EXPLORER_S3_BUCKET = 'thisismybucket.therearemanylikeit.butthisoneismine'
