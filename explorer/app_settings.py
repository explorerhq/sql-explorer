from django.conf import settings

EXPLORER_SQL_BLACKLIST = getattr(settings, 'EXPLORER_SQL_BLACKLIST', ('ALTER', 'RENAME ', 'DROP', 'TRUNCATE', 'INSERT INTO', 'UPDATE', 'REPLACE', 'DELETE', 'ALTER', 'CREATE TABLE', 'SCHEMA', 'GRANT', 'OWNER TO'))

EXPLORER_SQL_WHITELIST = getattr(settings, 'EXPLORER_SQL_WHITELIST', ('CREATED', 'DELETED'))

EXPLORER_DEFAULT_ROWS = getattr(settings, 'EXPLORER_DEFAULT_ROWS', 100)

EXPLORER_SCHEMA_EXCLUDE_APPS = getattr(settings, 'EXPLORER_SCHEMA_EXCLUDE_APPS', ('django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions', 'django.contrib.admin'))

EXPLORER_CONNECTION_NAME = getattr(settings, 'EXPLORER_CONNECTION_NAME', None)

EXPLORER_TRANSFORMS = getattr(settings, 'EXPLORER_TRANSFORMS', [])

EXPLORER_PERMISSION_VIEW = getattr(settings, 'EXPLORER_PERMISSION_VIEW', lambda u: u.is_staff)

EXPLORER_PERMISSION_CHANGE = getattr(settings, 'EXPLORER_PERMISSION_CHANGE', lambda u: u.is_staff)
