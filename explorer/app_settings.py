from pydoc import locate

from django.conf import settings


EXPLORER_CONNECTIONS = getattr(settings, "EXPLORER_CONNECTIONS", {})
EXPLORER_DEFAULT_CONNECTION = getattr(
    settings, "EXPLORER_DEFAULT_CONNECTION", None
)

# Change the behavior of explorer
EXPLORER_SQL_BLACKLIST = getattr(
    settings, "EXPLORER_SQL_BLACKLIST",
    (
        # DML
        "COMMIT",
        "DELETE",
        "INSERT",
        "MERGE",
        "REPLACE",
        "ROLLBACK",
        "SET",
        "START",
        "UPDATE",
        "UPSERT",

        # DDL
        "ALTER",
        "CREATE",
        "DROP",
        "RENAME",
        "TRUNCATE",

        # DCL
        "GRANT",
        "REVOKE",
    )
)


EXPLORER_DEFAULT_ROWS = getattr(settings, "EXPLORER_DEFAULT_ROWS", 1000)

EXPLORER_SCHEMA_EXCLUDE_TABLE_PREFIXES = getattr(
    settings,
    "EXPLORER_SCHEMA_EXCLUDE_TABLE_PREFIXES",
    (
        "auth_",
        "contenttypes_",
        "sessions_",
        "admin_"
    )
)

EXPLORER_SCHEMA_INCLUDE_TABLE_PREFIXES = getattr(
    settings,
    "EXPLORER_SCHEMA_INCLUDE_TABLE_PREFIXES",
    None
)
EXPLORER_SCHEMA_INCLUDE_VIEWS = getattr(
    settings,
    "EXPLORER_SCHEMA_INCLUDE_VIEWS",
    False
)

EXPLORER_TRANSFORMS = getattr(settings, "EXPLORER_TRANSFORMS", [])
EXPLORER_PERMISSION_VIEW = getattr(
    settings, "EXPLORER_PERMISSION_VIEW", lambda r: r.user.is_staff
)
EXPLORER_PERMISSION_CHANGE = getattr(
    settings, "EXPLORER_PERMISSION_CHANGE", lambda r: r.user.is_staff
)
EXPLORER_PERMISSION_CONNECTIONS = getattr(
    settings, "EXPLORER_PERMISSION_CONNECTIONS", lambda r: r.user.is_staff
)
EXPLORER_RECENT_QUERY_COUNT = getattr(
    settings, "EXPLORER_RECENT_QUERY_COUNT", 5
)
EXPLORER_ASYNC_SCHEMA = getattr(settings, "EXPLORER_ASYNC_SCHEMA", False)

DEFAULT_EXPORTERS = [
    ("csv", "explorer.exporters.CSVExporter"),
    ("json", "explorer.exporters.JSONExporter"),
]
try:
    import xlsxwriter  # noqa

    DEFAULT_EXPORTERS.insert(
        1,
        ("excel", "explorer.exporters.ExcelExporter"),
    )
except ImportError:
    pass

EXPLORER_DATA_EXPORTERS = getattr(
    settings, "EXPLORER_DATA_EXPORTERS", DEFAULT_EXPORTERS
)
CSV_DELIMETER = getattr(settings, "EXPLORER_CSV_DELIMETER", ",")

# API access
EXPLORER_TOKEN = getattr(settings, "EXPLORER_TOKEN", "CHANGEME")

# These are callable to aid testability by dodging the settings cache.
# There is surely a better pattern for this, but this'll hold for now.
EXPLORER_GET_USER_QUERY_VIEWS = lambda: getattr(  # noqa
    settings, "EXPLORER_USER_QUERY_VIEWS", {}
)
EXPLORER_TOKEN_AUTH_ENABLED = lambda: getattr(  # noqa
    settings, "EXPLORER_TOKEN_AUTH_ENABLED", False
)
EXPLORER_NO_PERMISSION_VIEW = lambda: locate(  # noqa
    getattr(
        settings,
        "EXPLORER_NO_PERMISSION_VIEW",
        "explorer.views.auth.safe_login_view_wrapper",
    ),
)

# Async task related. Note that the EMAIL_HOST settings must be set up for
# email to work.
ENABLE_TASKS = getattr(settings, "EXPLORER_TASKS_ENABLED", False)
S3_ACCESS_KEY = getattr(settings, "EXPLORER_S3_ACCESS_KEY", None)
S3_SECRET_KEY = getattr(settings, "EXPLORER_S3_SECRET_KEY", None)
S3_BUCKET = getattr(settings, "EXPLORER_S3_BUCKET", None)
S3_LINK_EXPIRATION: int = getattr(settings, "EXPLORER_S3_LINK_EXPIRATION", 3600)
FROM_EMAIL = getattr(
    settings, "EXPLORER_FROM_EMAIL", "django-sql-explorer@example.com"
)
S3_REGION = getattr(settings, "EXPLORER_S3_REGION", "us-east-1")
S3_ENDPOINT_URL = getattr(settings, "EXPLORER_S3_ENDPOINT_URL", None)
S3_DESTINATION = getattr(settings, "EXPLORER_S3_DESTINATION", "")
S3_SIGNATURE_VERSION = getattr(settings, "EXPLORER_S3_SIGNATURE_VERSION", "v4")

UNSAFE_RENDERING = getattr(settings, "EXPLORER_UNSAFE_RENDERING", False)

EXPLORER_CHARTS_ENABLED = getattr(settings, "EXPLORER_CHARTS_ENABLED", False)

EXPLORER_SHOW_SQL_BY_DEFAULT = getattr(settings, "EXPLORER_SHOW_SQL_BY_DEFAULT", True)

EXPLORER_ENABLE_ANONYMOUS_STATS = getattr(settings, "EXPLORER_ENABLE_ANONYMOUS_STATS", True)
EXPLORER_COLLECT_ENDPOINT_URL = "https://collect.sqlexplorer.io/stat"

# If set to True will autorun queries when viewed which is the historical behavior
# Default to True if not set in order to be backwards compatible
# If set to False will not autorun queries containing parameters when viewed
# - user will need to run by clicking the Save & Run Button to execute
EXPLORER_AUTORUN_QUERY_WITH_PARAMS = getattr(settings, "EXPLORER_AUTORUN_QUERY_WITH_PARAMS", True)
VITE_DEV_MODE = getattr(settings, "VITE_DEV_MODE", False)


# AI Assistant settings. Setting the first to an OpenAI key is the simplest way to enable the assistant
EXPLORER_AI_API_KEY = getattr(settings, "EXPLORER_AI_API_KEY", None)

EXPLORER_ASSISTANT_BASE_URL = getattr(settings, "EXPLORER_ASSISTANT_BASE_URL", "https://api.openai.com/v1")
EXPLORER_ASSISTANT_MODEL = getattr(settings, "EXPLORER_ASSISTANT_MODEL",
                                   # Return the model name and max_tokens it supports
                                   {"name": "gpt-4o",
                                    "max_tokens": 128000})

EXPLORER_DB_CONNECTIONS_ENABLED = getattr(settings, "EXPLORER_DB_CONNECTIONS_ENABLED", False)
EXPLORER_USER_UPLOADS_ENABLED = getattr(settings, "EXPLORER_USER_UPLOADS_ENABLED", False)
EXPLORER_PRUNE_LOCAL_UPLOAD_COPY_DAYS_INACTIVITY = getattr(settings,
                                                           "EXPLORER_PRUNE_LOCAL_UPLOAD_COPY_DAYS_INACTIVITY", 7)
# 500mb default max
EXPLORER_MAX_UPLOAD_SIZE = getattr(settings, "EXPLORER_MAX_UPLOAD_SIZE", 500 * 1024 * 1024)


def has_assistant():
    return EXPLORER_AI_API_KEY is not None


def db_connections_enabled():
    return EXPLORER_DB_CONNECTIONS_ENABLED


def user_uploads_enabled():
    return (EXPLORER_USER_UPLOADS_ENABLED and
            EXPLORER_DB_CONNECTIONS_ENABLED and
            S3_BUCKET is not None)
