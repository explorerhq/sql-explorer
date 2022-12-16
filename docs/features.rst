Features
========

Security
--------
- Let's not kid ourselves - this tool is all about giving people
  access to running SQL in production. So if that makes you
  nervous (**and it should**) - you've been warned. Explorer makes an
  effort to not allow terrible things to happen, but be careful!
  It's recommended you setup read-only roles for each of your database
  connections and only use these particular connections for your queries through the
  ``EXPLORER_CONNECTIONS`` setting.
- Explorer supports two different permission checks for users of
  the tool. Users passing the ``EXPLORER_PERMISSION_CHANGE`` test can
  create, edit, delete, and execute queries. Users who do not pass
  this test but pass the ``EXPLORER_PERMISSION_VIEW`` test can only
  execute queries. Other users cannot access any part of
  Explorer. Both permission groups are set to is_staff by default
  and can be overridden in your settings file.
- Enforces a SQL blacklist so destructive queries don't get
  executed (delete, drop, alter, update etc). This is not
  bulletproof and it's recommended that you instead configure a
  read-only database role, but when not possible the blacklist
  provides reasonable protection.

Easy to get started
-------------------
- Built on Django's ORM, so works with Postgresql, Mysql, and
  Sqlite. And, between you and me, it works fine on RedShift as
  well.
- Small number of dependencies.
- Just want to get in and write some ad-hoc queries? Go nuts with
  the Playground area.

Snapshots
---------
- Tick the 'snapshot' box on a query, and Explorer will upload a
  .csv snapshot of the query results to S3. Configure the snapshot
  frequency via a celery cron task, e.g. for daily at 1am:

.. code-block:: python

   'explorer.tasks.snapshot_queries': {
       'task': 'explorer.tasks.snapshot_queries',
       'schedule': crontab(hour=1, minute=0)
   }

- Requires celery, obviously. Also uses boto3. All
  of these deps are optional and can be installed with
  ``pip install "django-sql-explorer[snapshots]"``
- The checkbox for opting a query into a snapshot is ALL THE WAY
  on the bottom of the query view (underneath the results table).
- You must also have the setting ``EXPLORER_TASKS_ENABLED`` enabled.

Email query results
-------------------
- Click the email icon in the query listing view, enter an email
  address, and the query results (zipped .csv) will be sent to you
  asynchronously. Very handy for long-running queries.

Parameterized Queries
---------------------
- Use $$foo$$ in your queries and Explorer will build a UI to fill
  out parameters. When viewing a query like ``SELECT * FROM table
  WHERE id=$$id$$``, Explorer will generate UI for the ``id``
  parameter.
- Parameters are stashed in the URL, so you can share links to
  parameterized queries with colleagues
- Use ``$$paramName:defaultValue$$`` to provide default values for the
  parameters.

Schema Helper
-------------
- ``/explorer/schema/<connection-alias>`` renders a list of your table
  and column names + types that you can refer to while writing
  queries. Apps can be excluded from this list so users aren't
  bogged down with tons of irrelevant tables. See settings
  documentation below for details.
- This is available quickly as a sidebar helper while composing
  queries (see screenshot)
- Quick search for the tables you are looking for. Just start
  typing!
- Explorer uses Django DB introspection to generate the
  schema. This can sometimes be slow, as it issues a separate
  query for each table it introspects. Therefore, once generated,
  Explorer caches the schema information. There is also the option
  to generate the schema information asynchronously, via Celery. To
  enable this, make sure Celery is installed and configured, and
  set ``EXPLORER_ENABLE_TASKS`` and ``EXPLORER_ASYNC_SCHEMA`` to
  ``True``.

.. _Template Columns:

Template Columns
----------------
- Let's say you have a query like ``SELECT id, email FROM user`` and
  you'd like to quickly drill through to the profile page for each
  user in the result. You can create a ``template`` column to do
  just that.
- Just set up a template column in your settings file:

.. code-block:: python

   EXPLORER_TRANSFORMS = [
       ('user', '<a href="https://yoursite.com/profile/{0}/">{0}</a>')
   ]

- And change your query to ``SELECT id AS "user", email FROM
  user``. Explorer will match the ``user`` column alias to the
  transform and merge each cell in that column into the template
  string. `Cool!`
- Note you **must** set ``EXPLORER_UNSAFE_RENDERING`` to ``True`` if you
  want to see rendered HTML (vs string literals) in the output.
  And be aware of the implications of enabling that setting.

Pivot Table
-----------
- Go to the Pivot tab on query results to use the in-browser pivot
  functionality (provided by Pivottable JS).
- Hit the link icon on the top right to get a URL to recreate the
  exact pivot setup to share with colleagues.

Displaying query results as charts
----------------------------------

If the results table adheres to a certain format, the results can be displayed as a pie chart or a line chart.

To enable this feature, set ``EXPLORER_CHARTS_ENABLED`` setting to ``True`` and install the plotting libraries ``matplotlib`` and ``seaborn`` with

.. code-block:: console

   pip install "django-sql-explorer[charts]"

This will add the "Pie chart" and the "Line chart" tabs alongside the "Preview" and the "Pivot" tabs in the query results view.

The tabs show the respective charts if the query result table adheres to a format which the chart widget can read. Otherwise a message explaining the required format together with an example query is displayed.

Query Logs
----------
- Explorer will save a snapshot of every query you execute so you
  can recover lost ad-hoc queries, and see what you've been
  querying.
- This also serves as cheap-and-dirty versioning of Queries, and
  provides the 'run count' property and average duration in
  milliseconds, by aggregating the logs.
- You can also quickly share playground queries by copying the
  link to the playground's query log record -- look on the top
  right of the sql editor for the link icon.
- If Explorer gets a lot of use, the logs can get
  beefy. explorer.tasks contains the 'truncate_querylogs' task
  that will remove log entries older than <days> (30 days and
  older in the example below).

.. code-block:: python

   'explorer.tasks.truncate_querylogs': {
       'task': 'explorer.tasks.truncate_querylogs',
       'schedule': crontab(hour=1, minute=0),
       'kwargs': {'days': 30}
   }

Multiple Connections
--------------------
- Have data in more than one database? No problemo. Just set up
  multiple Django database connections, register them with
  Explorer, and you can write, save, and view queries against all
  of your different data sources. Compatible with any database
  support by Django. Note that the target database does *not* have
  to contain any Django schema, or be related to Django in any
  way. See connections.py for more documentation on
  multi-connection setup.

.. _Power tips:

Power tips
----------
- On the query listing page, focus gets set to a search box so you
  can just navigate to ``/explorer`` and start typing the name of your
  query to find it.
- Quick search also works after hitting "Show Schema" on a query
  view.
- Command+Enter and Ctrl+Enter will execute a query when typing in
  the SQL editor area.
- Hit the "Format" button to format and clean up your SQL (this is
  non-validating -- just formatting).
- If you find the "Format" button is not working, it may be due to the
  following setting ``CSRF_COOKIE_HTTPONLY = True`` which prevents
  client javascript from reading the CSRF cookie (see Django docs).
- Use the Query Logs feature to share one-time queries that aren't
  worth creating a persistent query for. Just run your SQL in the
  playground, then navigate to ``/logs`` and share the link
  (e.g. ``/explorer/play/?querylog_id=2428``)
- Click the 'history' link towards the top-right of a saved query
  to filter the logs down to changes to just that query.
- If you need to download a query as something other than csv but
  don't want to globally change delimiters via
  ``settings.EXPLORER_CSV_DELIMETER``, you can use
  ``/query/download?delim=|`` to get a pipe (or whatever) delimited
  file. For a tab-delimited file, use ``delim=tab``. Note that the
  file extension will remain .csv
- If a query is taking a long time to run (perhaps timing out) and
  you want to get in there to optimize it, go to
  ``/query/123/?show=0``. You'll see the normal query detail page, but
  the query won't execute.
- Set env vars for ``EXPLORER_TOKEN_AUTH_ENABLED=TRUE`` and
  ``EXPLORER_TOKEN=<SOME TOKEN>`` and you have an instant data
  API. Just:

.. code-block:: console

   curl --header "X-API-TOKEN: <TOKEN>" https://www.your-site.com/explorer/<QUERY_ID>/stream?format=csv

You can also pass the token with a query parameter like this:

.. code-block:: console

   curl https://www.your-site.com/explorer/<QUERY_ID>/stream?format=csv&token=<TOKEN>
