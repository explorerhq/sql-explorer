********
Settings
********

Here are all of the available settings with their default values.


SQL Blacklist
*************

Disallowed words in SQL queries to prevent destructive actions.

.. code-block:: python

   EXPLORER_SQL_BLACKLIST = (
        # DML
        'COMMIT',
        'DELETE',
        'INSERT',
        'MERGE',
        'REPLACE',
        'ROLLBACK',
        'SET',
        'START',
        'UPDATE',
        'UPSERT',

        # DDL
        'ALTER',
        'CREATE',
        'DROP',
        'RENAME',
        'TRUNCATE',

        # DCL
        'GRANT',
        'REVOKE',
    )



Default rows
************

The number of rows to show by default in the preview pane.

.. code-block:: python

   EXPLORER_DEFAULT_ROWS = 1000


Include table prefixes
**********************

If not ``None``, show schema only for tables starting with these prefixes. "Wins" if in conflict with ``EXCLUDE``

.. code-block:: python

   EXPLORER_SCHEMA_INCLUDE_TABLE_PREFIXES = None  # shows all tables


Exclude table prefixes
**********************

Don't show schema for tables starting with these prefixes, in the schema helper.

.. code-block:: python

   EXPLORER_SCHEMA_EXCLUDE_TABLE_PREFIXES = (
       'django.contrib.auth',
       'django.contrib.contenttypes',
       'django.contrib.sessions',
       'django.contrib.admin'
   )


Include views
*************

Include database views

.. code-block:: python

   EXPLORER_SCHEMA_INCLUDE_VIEWS = False


ASYNC schema
************
Generate DB schema asynchronously. Requires Celery and ``EXPLORER_TASKS_ENABLED``

.. code-block:: python

   EXPLORER_ASYNC_SCHEMA = False


Default connection
******************

The name of the Django database connection to use. Ideally set this to a connection with read only permissions

.. code-block:: python

   EXPLORER_DEFAULT_CONNECTION = None  # Must be set for the app to work, as this is required


Database connections
********************

A dictionary of ``{'Friendly Name': 'django_db_alias'}``.

.. code-block:: python

   EXPLORER_CONNECTIONS = {}  # At a minimum, should be set to something like { 'Default': 'readonly' } or similar. See connections.py for more documentation.


Permission view
****************
Callback to check if the user is allowed to view and execute stored queries

.. code-block:: python

   EXPLORER_PERMISSION_VIEW = lambda r: r.user.is_staff


Permission change
*****************

Callback to check if the user is allowed to add/change/delete queries

.. code-block:: python

   EXPLORER_PERMISSION_CHANGE = lambda r: r.user.is_staff


Transforms
**********

List of tuples, see :ref:`Template Columns` more info.

.. code-block:: python

   EXPLORER_TRANSFORMS = []


Recent query count
******************

The number of recent queries to show at the top of the query listing.

.. code-block:: python

   EXPLORER_RECENT_QUERY_COUNT = 10


User query views
****************

A dict granting view permissions on specific queries of the form

.. code-block:: python

   EXPLORER_GET_USER_QUERY_VIEWS = {userId:[queryId, ...], ...}

**Default Value:**

.. code-block:: python

   EXPLORER_GET_USER_QUERY_VIEWS = {}


Token Authentication
********************

Bool indicating whether token-authenticated requests should be enabled. See :ref:`Power Tips`.

.. code-block:: python

   EXPLORER_TOKEN_AUTH_ENABLED = False


Token
*****

Access token for query results.

.. code-block:: python

   EXPLORER_TOKEN = "CHANGEME"


Celery tasks
************

Turn on if you want to use the ``snapshot_queries`` celery task, or email report functionality in ``tasks.py``

.. code-block:: python

   EXPLORER_TASKS_ENABLED = False


S3 access key
*************

S3 Access Key for snapshot upload

.. code-block:: python

   EXPLORER_S3_ACCESS_KEY = None


S3 secret key
*************

S3 Secret Key for snapshot upload

.. code-block:: python

   EXPLORER_S3_SECRET_KEY = None


S3 bucket
*********

S3 Bucket for snapshot upload

.. code-block:: python

   EXPLORER_S3_BUCKET = None


S3 region
******************

S3 region. Defaults to us-east-1 if not specified.

.. code-block:: python

   EXPLORER_S3_REGION = 'us-east-1'



S3 endpoint url
******************

S3 endpoint url. Normally not necessary to set.
Useful to set if you are using a non-AWS S3 service or you are using a private AWS endpoint.


.. code-block:: python

   EXPLORER_S3_ENDPOINT_URL = 'https://accesspoint.vpce-abc123-abcdefgh.s3.us-east-1.vpce.amazonaws.com'



S3 link expiration
******************

S3 link expiration time. Defaults to 3600 seconds (1hr) if not specified.
Links are generated as presigned urls for security

.. code-block:: python

   EXPLORER_S3_LINK_EXPIRATION = 3600


From email
**********

The default 'from' address when using async report email functionality

.. code-block:: python

   EXPLORER_FROM_EMAIL = "django-sql-explorer@example.com"


Data exporters
**************

The export buttons to use. Default includes Excel, so xlsxwriter from ``requirements/optional.txt`` is needed

.. code-block:: python

   EXPLORER_DATA_EXPORTERS = [
       ('csv', 'explorer.exporters.CSVExporter'),
       ('excel', 'explorer.exporters.ExcelExporter'),
       ('json', 'explorer.exporters.JSONExporter')
   ]


Unsafe rendering
*****************************

Disable auto escaping for rendering values from the database. Be wary of XSS attacks if querying unknown data.

.. code-block:: python

   EXPLORER_UNSAFE_RENDERING = False


No permission view
******************

Path to a view used when the user does not have permission. By default, a basic login view is provided
but a dotted path to a python view can be used

.. code-block:: python

   EXPLORER_NO_PERMISSION_VIEW = 'explorer.views.auth.safe_login_view_wrapper'
