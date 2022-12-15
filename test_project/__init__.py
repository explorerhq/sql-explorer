try:
    from .celery_config import app as celery_app

    __all__ = ['celery_app']
except ImportError:
    pass
