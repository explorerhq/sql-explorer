import sys
from django.conf import settings

# Required
EXPLORER_CONNECTION_NAME = getattr(settings, 'EXPLORER_CONNECTION_NAME', None)

# Change the behavior of explorer
EXPLORER_SQL_BLACKLIST = getattr(settings, 'EXPLORER_SQL_BLACKLIST', ('ALTER',
                                                                      'RENAME ',
                                                                      'DROP',
                                                                      'TRUNCATE',
                                                                      'INSERT INTO',
                                                                      'UPDATE',
                                                                      'REPLACE',
                                                                      'DELETE',
                                                                      'CREATE TABLE',
                                                                      'GRANT',
                                                                      'OWNER TO'))

EXPLORER_SQL_WHITELIST = getattr(settings, 'EXPLORER_SQL_WHITELIST', ('CREATED',
                                                                      'UPDATED',
                                                                      'DELETED',
                                                                      'REGEXP_REPLACE'))

EXPLORER_DEFAULT_ROWS = getattr(settings, 'EXPLORER_DEFAULT_ROWS', 1000)

EXPLORER_SCHEMA_EXCLUDE_TABLE_PREFIXES = getattr(settings, 'EXPLORER_SCHEMA_EXCLUDE_TABLE_PREFIXES', ('auth_',
                                                                                                      'contenttypes_',
                                                                                                      'sessions_',
                                                                                                      'admin_'))

EXPLORER_SCHEMA_INCLUDE_TABLE_PREFIXES = getattr(settings, 'EXPLORER_SCHEMA_INCLUDE_TABLE_PREFIXES', None)

EXPLORER_TRANSFORMS = getattr(settings, 'EXPLORER_TRANSFORMS', [])
EXPLORER_PERMISSION_VIEW = getattr(settings, 'EXPLORER_PERMISSION_VIEW', lambda u: u.is_staff)
EXPLORER_PERMISSION_CHANGE = getattr(settings, 'EXPLORER_PERMISSION_CHANGE', lambda u: u.is_staff)
EXPLORER_RECENT_QUERY_COUNT = getattr(settings, 'EXPLORER_RECENT_QUERY_COUNT', 10)

EXPLORER_DATA_EXPORTERS = getattr(settings, 'EXPLORER_DATA_EXPORTERS', [
    ('csv', 'explorer.exporters.CSVExporter'),
    ('excel', 'explorer.exporters.ExcelExporter'),
    ('json', 'explorer.exporters.JSONExporter'),

])

EXPLORER_SCHEMA_BUILDERS = getattr(settings, 'EXPLORER_SCHEMA_BUILDERS', [
    ('sqlite', 'explorer.schema.SQLiteSchema'),
    ('postgresql', 'explorer.schema.PostgreSQLSchema'),
    ('mysql', 'explorer.schema.MySQLSchema')
])
   
if sys.version_info[0] < 3:
    try:
        # Add pdf export iff python version < 3 and django-xhtml2pdf is installed
        from django_xhtml2pdf.utils import generate_pdf
        EXPLORER_DATA_EXPORTERS += (
            ('pdf', 'explorer.exporters.PdfExporter'),
        )
    except:
        pass

CSV_DELIMETER = getattr(settings, "EXPLORER_CSV_DELIMETER", ",")

# API access
EXPLORER_TOKEN = getattr(settings, 'EXPLORER_TOKEN', 'CHANGEME')

# These are callable to aid testability by dodging the settings cache.
# There is surely a better pattern for this, but this'll hold for now.
EXPLORER_GET_USER_QUERY_VIEWS = lambda: getattr(settings, 'EXPLORER_USER_QUERY_VIEWS', {})
EXPLORER_TOKEN_AUTH_ENABLED = lambda: getattr(settings, 'EXPLORER_TOKEN_AUTH_ENABLED', False)

# Async task related. Note that the EMAIL_HOST settings must be set up for email to work.
ENABLE_TASKS = getattr(settings, "EXPLORER_TASKS_ENABLED", False)
S3_ACCESS_KEY = getattr(settings, "EXPLORER_S3_ACCESS_KEY", None)
S3_SECRET_KEY = getattr(settings, "EXPLORER_S3_SECRET_KEY", None)
S3_BUCKET = getattr(settings, "EXPLORER_S3_BUCKET", None)
FROM_EMAIL = getattr(settings, 'EXPLORER_FROM_EMAIL', 'django-sql-explorer@example.com')

UNSAFE_RENDERING = getattr(settings, "EXPLORER_UNSAFE_RENDERING", False)
