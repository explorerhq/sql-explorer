from django.conf import settings

from celery import Celery

app = Celery('test_project')

app.config_from_object(
    'django.conf:settings',
    namespace='CELERY'
)

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
