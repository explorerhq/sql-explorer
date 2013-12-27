from django.conf import settings

SQL_BLACKLIST = getattr(settings, 'SQL_BLACKLIST', ('ALTER', 'RENAME ', 'DROP', 'TRUNCATE', 'INSERT INTO', 'UPDATE', 'REPLACE', 'DELETE'))

SQL_WHITELIST = getattr(settings, 'SQL_WHITELIST', ('DROP FUNCTION', 'REPLACE FUNCTION', 'DROP VIEW', 'REPLACE VIEW', 'CREATED', 'DELETED'))

REPORT_LOGGER_NAME = getattr(settings, 'REPORT_LOGGER_NAME', 'django')