==========
Change Log
==========

This document records all notable changes to `SQL Explorer <https://github.com/explorerhq/sql-explorer>`_.
This project adheres to `Semantic Versioning <https://semver.org/>`_.

vNext
===========================
* `#664`_: Improvements to the AI SQL Assistant:

  - Table Annotations: Write persistent table annotations with descriptive information that will get injected into the
    prompt for the assistant. For example, if a table is commonly joined to another table through a non-obvious foreign
    key, you can tell the assistant about it in plain english, as an annotation to that table. Every time that table is
    deemed 'relevant' to an assistant request, that annotation will be included alongside the schema and sample data.
  - Few-Shot Examples: Using the small checkbox on the bottom-right of any saved queries, you can designate certain
    queries as 'few shot examples". When making an assistant request, any designated few-shot examples that reference
    the same tables as your assistant request will get included as 'reference sql' in the prompt for the LLM.
  - Autocomplete / multiselect when selecting tables info to send to the SQL Assistant. Much easier and more keyboard
    focused.
  - Relevant tables are added client-side visually, in real time, based on what's in the SQL editor and/or any tables
    mentioned in the assistant request. The dependency on sql_metadata is therefore removed, as server-side SQL parsing
    is no longer necessary.
  - Ability to view Assistant request/response history.
  - Improved system prompt that emphasizes the particular SQL dialect being used.
  - Addresses issue #657.

* `#660`_: Userspace connection migration.

  - This should be an invisible change, but represents a significant refactor of how connections function. Instead of a
    weird blend of DatabaseConnection models and underlying Django models (which were the original Explorer
    connections), this migrates all connections to DatabaseConnection models and implements proper foreign keys to them
    on the Query and QueryLog models. A data migration creates new DatabaseConnection models based on the configured
    settings.EXPLORER_CONNECTIONS. Going forward, admins can create new Django-backed DatabaseConnection models by
    registering the connection in EXPLORER_CONNECTIONS, and then creating a DatabaseConnection model using the Django
    admin or the user-facing /connections/new/ form, and entering the Django DB alias and setting the connection type
    to "Django Connection".
  - The Query.connection and QueryLog.connection fields are deprecated and will be removed in a future release. They
    are kept around in this release in case there is an unforeseen issue with the migration. Preserving the fields for
    now ensures there is no data loss in the event that a rollback to an earlier version is required.

* Fixed a bug when validating connections to uploaded files. Also added basic locking when downloading files from S3.

* Keyboard shortcut for formatting the SQL in the editor.

  - Cmd+Shift+F (Windows: Ctrl+Shift+F)
  - The format button has been moved tobe a small icon towards the bottom-right of the SQL editor.

`5.2.0`_ (2024-08-19)
===========================
* `#651`_: Ability to append an upload to a previously uploaded file/sqlite DB as a new table

  * Good cache busting and detection of file changes on uploads
  * Significant documentation improvements to uploads and connections
  * Separate the upload UI from the 'add connection' UI, as they are materially different
  * Fix a small bug with bar chart generation, when values are null
  * Ability to refresh a connection's schema and data (if it's an upload) from the connections list view

* `#659`_: Search all queries, even if the header is collapsed. Addresses issue #464 (partially) and #658 (fully).
* `#662`_: Refactored dockerfile to use non-root directories. Addresses issue #661.


`5.1.1`_ (2024-07-30)
===========================
* `#654`_: Bugfix: Parameterized query does not work for viewers
* `#653`_: Bugfix: Schema search not visible anymore
* Bugfix: Error messages in query.html were floating in the wrong spot
* `#555`_: Prevent queries with many thousands of results from being punishingly slow. The number of data points in
  the chart now matches the number of data points in the preview pane.

`5.1.0`_ (2024-07-30)
===========================
Major improvements:

* `#647`_: Upload json files as data sources (in addition to CSV and SQLite files). Both 'normal'
  json files, and files structured as a list of json objects (one json object per line) are supported.
* `#643`_: Addresses #640 (Snowflake support). Additionally, supports an "extras" field on the
  userspace DatabaseConnection object, which allows for arbitrary additional connection
  params to get added. This allows engine-specific (or just more obscure) settings to
  get injected into the connection.
* `#644`_: Dockerfile and docker-compose to run the test_project. Replaces the old start.sh script.

Minor improvements:

* `#647`_: In the schema explorer, clicking on a field name copies it to the clipboard
* `#647`_: Charts are limited to a maximum of 10 series. This significantly speeds up rendering
  of 'wide' result-sets when charts are enabled.
* `#645`_: Removed pie charts, added bar charts. Replaced Seaborn with Matplotlib
  because it's much lighter weight. Pie charts were overly finicky to get working.
  Bars are more useful. Will look to continue to expand charting in the future.
* `#643`_: After uploading a csv/json/etc, the resulting connection is highlighted in the
  connection list, making it much clearer what happened.
* `#643`_: Fixed some bugs in user connection stuff in general, and improved the UI.

Bugfixes and internal improvements:

* `#647`_: Robustness to the user uploads feature, in terms of the UI, error handling and logging, and test coverage.
* `#648`_: Backwards migration for 0016_alter_explorervalue_key.py
* `#649`_: Use a more reliable source of the static files URL
* `#635`_: Improved test coverage in tox, so that base requirements are properly used.
  This would have prevented (for example) issue 631. Additionally, introduced a test
  to verify that migrations are always generated, which would have prevented #633.
* `#636`_: Output rendering bugfix.
* `#567`_: Upgrade translate tags in templates to more modern style.

`5.0.2`_ (2024-07-3)
===========================
* `#633`_: Missing migration
* CSS tweaks to tighten up the Query UI

`5.0.1`_ (2024-06-26)
===========================
* `#631`_: Pandas is only required if EXPLORER_USER_UPLOADS_ENABLED is True

`5.0.0`_ (2024-06-25)
===========================

* Manage DB connections via the UI (and/or Django Admin). Set EXPLORER_DB_CONNECTIONS_ENABLED
  to True in settings to enable user-facing connection management.
* Upload CSV or SQLite DBs directly, to create additional connections.
  This functionality has additional dependencies which can be installed with
  the 'uploads' extra (e.g. pip install django-sql-explorer[uploads]). Then set EXPLORER_USER_UPLOADS_ENABLED
  to True, and make sure S3_BUCKET is also set up.
* The above functionality is managed by a new license, restricting the
  ability of 3rd parties resell SQL Explorer (commercial usage is absolutely
  still permitted).
* Query List home page is sortable
* Select all / deselect all with AI assistant
* Assistant tests run reliably in CI/CD
* Introduced some branding and styling improvements


`4.3.0`_ (2024-05-27)
===========================

* Keyboard shortcut to show schema hints (cmd+S / ctrl+S -- note that is a capital
  "S" so the full kbd commands is cmd+shift+s)
* DB-managed LLM prompts (editable in django admin)
* Versioned .js bundles (for cache busting)
* Automatically populate assistant responses that contain code into the editor
* `#616`_: Update schema/assistant tables/autocomplete on connection drop-down change
* `#618`_: Import models so that migrations are properly understood by Django
* `#619`_: Get CSRF from DOM (instead of cookie) if CSRF_USE_SESSIONS is set

`4.2.0`_ (2024-04-26)
===========================
* `#609`_: Tracking should be opt-in and not use the SECRET_KEY
* `#610`_: Import error (sql_metadata) with 4.1 version
* `#612`_: Accessing the database during app initialization
* Regex-injection vulnerability
* Improved assistant UI

`4.1.0`_ (2024-04-23)
===========================
* SQL Assistant: Built in query help via OpenAI (or LLM of choice), with relevant schema
  automatically injected into the prompt. Enable by setting EXPLORER_AI_API_KEY.
* Anonymous usage telemetry. Disable by setting EXPLORER_ENABLE_ANONYMOUS_STATS to False.
* Refactor pip requirements to make 'extras' more robust and easier to manage.
* `#592`_: Support user models with no email fields
* `#594`_: Eliminate <script> tags to prevent potential Content Security Policy issues.

`4.0.2`_ (2024-02-06)
===========================
* Add support for Django 5.0. Drop support for Python < 3.10.
* Basic code completion in the editor!
* Front-end must be built with Vite if installing from source.
* `#565`_: Front-end modernization. CodeMirror 6. Bootstrap5. Vite-based build
* `#566`_: Django 5 support & tests
* `#537`_: S3 signature version support
* `#562`_: Record and show whether the last run of each query was successful
* `#571`_: Replace isort and flake8 with Ruff (linting)

`4.0.0.beta1`_ (2024-02-01)
===========================
* Yanked due to a packaging version issue

`3.2.1`_ (2023-07-13)
=====================
* `#539`_: Test for SET PASSWORD
* `#544`_: Fix `User` primary key reference

`3.2.0`_ (2023-05-17)
=====================
* `#533`_: CSRF token httponly support + s3 destination for async results

`3.1.1`_ (2023-02-27)
=====================
* `#529`_: Added ``makemigrations --check`` pre-commit hook
* `#528`_: Add missing migration

`3.1.0`_ (2023-02-25)
=====================
* `#520`_: Favorite queries
* `#519`_: Add labels to params like ``$$paramName|label:defaultValue$$``
* `#517`_: Pivot export

* `#524`_: ci: pre-commit autoupdate
* `#523`_: ci: ran pre-commit on all files for ci bot integration
* `#522`_: ci: coverage update
* `#521`_: ci: Adding django 4.2 to the test suite

`3.0.1`_ (2022-12-16)
=====================
* `#515`_: Fix for running without optional packages

`3.0`_ (2022-12-15)
===================
* Add support for Django >3.2 and drop support for <3.2
* Add support for Python 3.9, 3.10 and 3.11 and drop support for <3.8
* `#496`_: Document breakage of "Format" button due to ``CSRF_COOKIE_HTTPONLY`` (`#492`_)
* `#497`_: Avoid execution of parameterised queries when viewing query
* `#498`_: Change sql blacklist functionality from regex to sqlparse
* `#500`_: Form display in popup now requires sanitize: false flag
* `#501`_: Updated celery support
* `#504`_: Added pre-commit hooks
* `#505`_: Feature/more s3 providers
* `#506`_: Check sql blacklist on execution as well as save
* `#508`_: Conditionally import optional packages

`2.5.0`_ (2022-10-09)
=====================
* `#494`_: Fixes Security hole in blacklist for MySQL (`#490`_)
* `#488`_: docs: Fix a few typos
* `#481`_: feat: Add pie and line chart tabs to query result preview
* `#478`_: feat: Improved templates to make easier to customize (Fix `#477`_)


`2.4.2`_ (2022-08-30)
=====================
* `#484`_: Added ``DEFAULT_AUTO_FIELD`` (Fix `#483`_)
* `#475`_: Add ``SET`` to blacklisted keywords

`2.4.1`_ (2022-03-10)
=====================
* `#471`_: Fix extra white space in description and SQL fields.

`2.4.0`_ (2022-02-10)
=====================
* `#470`_: Upgrade JS/CSS versions.

`2.3.0`_ (2021-07-24)
=====================
* `#450`_: Added Russian translations.
* `#449`_: Translates expression for duration

`2.2.0`_ (2021-06-14)
=====================
* Updated docs theme to `furo`_
* `#445`_: Added ``EXPLORER_NO_PERMISSION_VIEW`` setting to allow override of the "no permission" view (Fix `#440`_)
* `#444`_: Updated structure of the settings docs (Fix `#443`_)

`2.1.3`_ (2021-05-14)
=====================
* `#442`_: ``GET`` params passed to the fullscreen view (Fix `#433`_)
* `#441`_: Include BOM in CSV export (Fix `#430`_)

`2.1.2`_ (2021-01-19)
=====================
* `#431`_: Fix for hidden SQL panel on a new query

`2.1.1`_ (2021-01-19)
=====================
Mistake in release

`2.1.0`_ (2021-01-13)
=====================

* **BREAKING CHANGE**: ``request`` object now passed to ``EXPLORER_PERMISSION_CHANGE`` and ``EXPLORER_PERMISSION_VIEW`` (`#417`_ to fix `#396`_)

Major Changes

* `#413`_: Static assets now served directly from the application, not CDN. (`#418`_ also)
* `#414`_: Better blacklist checking - Fix `#371`_ and `#412`_
* `#415`_: Fix for MySQL following change for Oracle in `#337`_

Minor Changes

* `#370`_: Get the CSRF cookie name from django instead of a hardcoded value
* `#410`_ and `#416`_: Sphinx docs
* `#420`_: Formatting change in templates
* `#424`_: Collapsable SQL panel
* `#425`_: Ensure a `Query` object contains SQL


`2.0.0`_ (2020-10-09)
=====================

* **BREAKING CHANGE**: #403: Dropping support for EOL `Python 2.7 <https://www.python.org/doc/sunset-python-2/>`_ and `3.5 <https://pythoninsider.blogspot.com/2020/10/python-35-is-no-longer-supported.html>`_

Major Changes

* `#404`_: Add support for Django 3.1 and drop support for (EOL) <2.2
* `#408`_: Refactored the application, updating the URLs to use path and the views into a module

Minor Changes

* `#334`_: Django 2.1 support
* `#337`_: Fix Oracle query failure caused by `TextField` in a group by clause
* `#345`_: Added (some) Chinese translation
* `#366`_: Changes to Travis django versions
* `#372`_: Run queries as atomic requests
* `#382`_: Django 2.2 support
* `#383`_: Typo in the README
* `#385`_: Removed deprecated `render_to_response` usage
* `#386`_: Bump minimum django version to 2.2
* `#387`_: Django 3 support
* `#390`_: README formatting changes
* `#393`_: Added option to install `XlsxWriter` as an extra package
* `#397`_: Bump patch version of django 2.2
* `#406`_: Show some love to the README
* Fix `#341`_: PYC files excluded from build


`1.1.3`_ (2019-09-23)
=====================

* `#347`_: URL-friendly parameter encoding
* `#354`_: Updating dependency reference for Python 3 compatibility
* `#357`_: Include database views in list of tables
* `#359`_: Fix unicode issue when generating migration with py2 or py3
* `#363`_: Do not use "message" attribute on exception
* `#368`_: Update EXPLORER_SCHEMA_EXCLUDE_TABLE_PREFIXES

Minor Changes

* release checklist included in repo
* readme updated with new screenshots
* python dependencies/optional-dependencies updated to latest (six, xlsxwriter, factory-boy, sqlparse)


`1.1.2`_ (2018-08-14)
=====================

* Fix `#269`_
* Fix bug when deleting query
* Fix bug when invalid characters present in Excel worksheet name

Major Changes

* Django 2.0 compatibility
* Improved interface to database connection management

Minor Changes

* Documentation updates
* Load images over same protocol as originating page


`1.1.1`_ (2017-03-21)
=====================

* Fix `#288`_ (incorrect import)


`1.1.0`_ (2017-03-19)
=====================

* **BREAKING CHANGE**: ``EXPLORER_DATA_EXPORTERS`` setting is now a list of tuples instead of a dictionary.
  This only affects you if you have customized this setting. This was to preserve ordering of the export buttons in the UI.
* **BREAKING CHANGE**: Values from the database are now escaped by default. Disable this behavior (enabling potential XSS attacks)
  with the ``EXPLORER_UNSAFE_RENDERING setting``.

Major Changes

* Django 1.10 and 2.0 compatibility
* Theming & visual updates
* PDF export
* Query-param based authentication (`#254`_)
* Schema built via SQL querying rather than Django app/model introspection. Paves the way for the tool to be pointed at any DB, not just Django DBs

Minor Changes

* Switched from TinyS3 to Boto (will switch to Boto3 in next release)
* Optionally show row numbers in results preview pane
* Full-screen view (icon on top-right of preview pane)
* Moved 'open in playground' to icon on top-right on SQL editor
* Save-only option (does not execute query)
* Show the time that the query was rendered (useful if you've had a tab open a while)


`1.0.0`_ (2016-06-16)
=====================

* **BREAKING CHANGE**: Dropped support for Python 2.6. See ``.travis.yml`` for test matrix.
* **BREAKING CHANGE**: The 'export' methods have all changed. Those these weren't originally designed to be external APIs,
  folks have written consuming code that directly called export code.

  If you had code that looked like:

      ``explorer.utils.csv_report(query)``

  You will now need to do something like:

      ``explorer.exporters.get_exporter_class('csv')(query).get_file_output()``

* There is a new export system! v1 is shipping with support for CSV, JSON, and Excel (xlsx). The availablility of these can be configured via the EXPLORER_DATA_EXPORTERS setting.
  * `Note` that for Excel export to work, you will need to install ``xlsxwriter`` from ``optional-requirements.txt.``
* Introduced Query History link. Find it towards the top right of a saved query.
* Front end performance improvements and library upgrades.
* Allow non-admins with permission to log into explorer.
* Added a proper test_project for an easier entry-point for contributors, or folks who want to kick the tires.
* Loads of little bugfixes.

`0.9.2`_ (2016-02-02)
=====================

* Fixed readme issue (.1) and ``setup.py`` issue (.2)

`0.9.1`_ (2016-02-01)
=====================

Major changes

* Dropped support for Django 1.6, added support for Django 1.9.
  See .travis.yml for test matrix.
* Dropped charted.js & visualization because it didn't work well.
* Client-side pivot tables with pivot.js. This is ridiculously cool!

Minor (but awesome!) changes

* Cmd-/ to comment/uncomment a block of SQL
* Quick 'shortcut' links to the corresponding querylog to more quickly share results.
  Look at the top-right of the editor. Also works for playground!
* Prompt for unsaved changes before navigating away
* Support for default parameter values via $$paramName:defaultValue$$
* Optional Celery task for truncating query logs as entries build up
* Display historical average query runtime

* Increased default number of rows from 100 to 1000
* Increased SQL editor size (5 additional visible lines)
* CSS cleanup and streamlining (making better use of foundation)
* Various bugfixes (blacklist not enforced on playground being the big one)
* Upgraded front-end libraries
* Hide Celery-based features if tasks not enabled.

`0.8.0`_ (2015-10-21)
=====================

* Snapshots! Dump the csv results of a query to S3 on a regular schedule.
  More details in readme.rst under 'features'.
* Async queries + email! If you have a query that takes a long time to run, execute it in the background and
  Explorer will send you an email with the results when they are ready. More details in readme.rst
* Run counts! Explorer inspects the query log to see how many times a query has been executed.
* Column Statistics! Click the ... on top of numeric columns in the results pane to see min, max, avg, sum, count, and missing values.
* Python 3! * Django 1.9!
* Delimiters! Export with delimiters other than commas.
* Listings respect permissions! If you've given permission to queries to non-admins,
  they will see only those queries on the listing page.

`0.7.0`_ (2015-02-18)
=====================

* Added search functionality to schema view and explorer view (using list.js).
* Python 2.6 compatibility.
* Basic charts via charted (from Medium via charted.co).
* SQL formatting function.
* Token authentication to retrieve csv version of queries.
* Fixed south_migrations packaging issue.
* Refactored front-end and pulled CSS and JS into dedicated files.

`0.6.0`_ (2014-11-05)
=====================

* Introduced Django 1.7 migrations. See readme.rst for info on how to run South migrations if you are not on Django 1.7 yet.
* Upgraded front-end libraries to latest versions.
* Added ability to grant selected users view permissions on selected queries via the ``EXPLORER_USER_QUERY_VIEWS`` parameter
* Example usage: ``EXPLORER_USER_QUERY_VIEWS = {1: [3,4], 2:[3]}``
* This would grant user with PK 1 read-only access to query with PK=3 and PK=4 and user 2 access to query 3.
* Bugfixes
* Navigating to an explorer URL without the trailing slash now redirects to the intended page (e.g. ``/logs`` -> ``/logs/``)
* Downloading a .csv and subsequently re-executing a query via a keyboard shortcut (cmd+enter) would re-submit the form and re-download the .csv. It now correctly just refreshes the query.
* Django 1.7 compatibility fix

`0.5.1`_ (2014-09-02)
=====================

Bugfixes

* Created_by_user not getting saved correctly
* Content-disposition .csv issue
* Issue with queries ending in ``...like '%...`` clauses
* Change the way customer user model is referenced

* Pseudo-folders for queries. Use "Foo * Ba1", "Foo * Bar2" for query names and the UI will build a little "Foo" pseudofolder for you in the query list.

`0.5.0`_ (2014-06-06)
=====================

* Query logs! Accessible via ``explorer/logs/``. You can look at previously executed queries (so you don't, for instance,
  lose that playground query you were working, or have to worry about mucking up a recorded query).
  It's quite usable now, and could be used for versioning and reverts in the future. It can be accessed at ``explorer/logs/``
* Actually captures the creator of the query via a ForeignKey relation, instead of just using a Char field.
* Re-introduced type information in the schema helpers.
* Proper relative URL handling after downloading a query as CSV.
* Users with view permissions can use query parameters. There is potential for SQL injection here.
  I think about the permissions as being about preventing users from borking up queries, not preventing them from viewing data.
  You've been warned.
* Refactored params handling for extra safety in multi-threaded environments.

`0.4.1`_ (2014-02-24)
=====================

* Renaming template blocks to prevent conflicts

`0.4`_ (2014-02-14 `Happy Valentine's Day!`)
============================================

* Templatized columns for easy linking
* Additional security config options for splitting create vs. view permissions
* Show many-to-many relation tables in schema helper

`0.3`_ (2014-01-25)
-------------------

* Query execution time shown in query preview
* Schema helper available as a sidebar in the query views
* Better defaults for sql blacklist
* Minor UI bug fixes

`0.2`_ (2014-01-05)
-------------------

* Support for parameters
* UI Tweaks
* Test coverage

`0.1.1`_ (2013-12-31)
=====================

Bug Fixes

* Proper SQL blacklist checks
* Downloading CSV from playground

`0.1`_ (2013-12-29)
-------------------

Initial Release

.. _0.1: https://github.com/explorerhq/sql-explorer/tree/0.1
.. _0.1.1: https://github.com/explorerhq/sql-explorer/compare/0.1...0.1.1
.. _0.2: https://github.com/explorerhq/sql-explorer/compare/0.1.1...0.2
.. _0.3: https://github.com/explorerhq/sql-explorer/compare/0.2...0.3
.. _0.4: https://github.com/explorerhq/sql-explorer/compare/0.3...0.4
.. _0.4.1: https://github.com/explorerhq/sql-explorer/compare/0.4...0.4.1
.. _0.5.0: https://github.com/explorerhq/sql-explorer/compare/0.4.1...0.5.0
.. _0.5.1: https://github.com/explorerhq/sql-explorer/compare/0.5.0...541148e7240e610f01dd0c260969c8d56e96a462
.. _0.6.0: https://github.com/explorerhq/sql-explorer/compare/0.5.0...0.6.0
.. _0.7.0: https://github.com/explorerhq/sql-explorer/compare/0.6.0...0.7.0
.. _0.8.0: https://github.com/explorerhq/sql-explorer/compare/0.7.0...0.8.0
.. _0.9.1: https://github.com/explorerhq/sql-explorer/compare/0.9.0...0.9.1
.. _0.9.2: https://github.com/explorerhq/sql-explorer/compare/0.9.1...0.9.2
.. _1.0.0: https://github.com/explorerhq/sql-explorer/compare/0.9.2...1.0.0

.. _1.1.0: https://github.com/explorerhq/sql-explorer/compare/1.0.0...1.1.1
.. _1.1.1: https://github.com/explorerhq/sql-explorer/compare/1.1.0...1.1.1
.. _1.1.2: https://github.com/explorerhq/sql-explorer/compare/1.1.1...1.1.2
.. _1.1.3: https://github.com/explorerhq/sql-explorer/compare/1.1.2...1.1.3
.. _2.0.0: https://github.com/explorerhq/sql-explorer/compare/1.1.3...2.0
.. _2.1.0: https://github.com/explorerhq/sql-explorer/compare/2.0...2.1.0
.. _2.1.1: https://github.com/explorerhq/sql-explorer/compare/2.1.0...2.1.1
.. _2.1.2: https://github.com/explorerhq/sql-explorer/compare/2.1.1...2.1.2
.. _2.1.3: https://github.com/explorerhq/sql-explorer/compare/2.1.2...2.1.3
.. _2.2.0: https://github.com/explorerhq/sql-explorer/compare/2.1.3...2.2.0
.. _2.3.0: https://github.com/explorerhq/sql-explorer/compare/2.2.0...2.3.0
.. _2.4.0: https://github.com/explorerhq/sql-explorer/compare/2.3.0...2.4.0
.. _2.4.1: https://github.com/explorerhq/sql-explorer/compare/2.4.0...2.4.1
.. _2.4.2: https://github.com/explorerhq/sql-explorer/compare/2.4.1...2.4.2
.. _2.5.0: https://github.com/explorerhq/sql-explorer/compare/2.4.2...2.5.0
.. _3.0: https://github.com/explorerhq/sql-explorer/compare/2.5.0...3.0
.. _3.0.1: https://github.com/explorerhq/sql-explorer/compare/3.0...3.0.1
.. _3.1.0: https://github.com/explorerhq/sql-explorer/compare/3.0.1...3.1.0
.. _3.1.1: https://github.com/explorerhq/sql-explorer/compare/3.1.0...3.1.1
.. _3.2.0: https://github.com/explorerhq/sql-explorer/compare/3.1.1...3.2.0
.. _3.2.1: https://github.com/explorerhq/sql-explorer/compare/3.2.0...3.2.1
.. _4.0.0.beta1: https://github.com/explorerhq/sql-explorer/compare/3.2.1...4.0.0.beta1
.. _4.0.2: https://github.com/explorerhq/sql-explorer/compare/4.0.0...4.0.2
.. _4.1.0: https://github.com/explorerhq/sql-explorer/compare/4.0.2...4.1.0
.. _4.2.0: https://github.com/explorerhq/sql-explorer/compare/4.1.0...4.2.0
.. _4.3.0: https://github.com/explorerhq/sql-explorer/compare/4.2.0...4.3.0
.. _5.0.0: https://github.com/explorerhq/sql-explorer/compare/4.3.0...5.0.0
.. _5.0.1: https://github.com/explorerhq/sql-explorer/compare/5.0.0...5.0.1
.. _5.0.2: https://github.com/explorerhq/sql-explorer/compare/5.0.1...5.0.2
.. _5.1.0: https://github.com/explorerhq/sql-explorer/compare/5.0.2...5.1.0
.. _5.1.1: https://github.com/explorerhq/sql-explorer/compare/5.1.0...5.1.1
.. _5.2b1: https://github.com/explorerhq/sql-explorer/compare/5.1.1...5.2.0


.. _#254: https://github.com/explorerhq/sql-explorer/pull/254
.. _#334: https://github.com/explorerhq/sql-explorer/pull/334
.. _#337: https://github.com/explorerhq/sql-explorer/pull/337
.. _#345: https://github.com/explorerhq/sql-explorer/pull/345
.. _#347: https://github.com/explorerhq/sql-explorer/pull/347
.. _#354: https://github.com/explorerhq/sql-explorer/pull/354
.. _#357: https://github.com/explorerhq/sql-explorer/pull/357
.. _#359: https://github.com/explorerhq/sql-explorer/pull/359
.. _#363: https://github.com/explorerhq/sql-explorer/pull/363
.. _#366: https://github.com/explorerhq/sql-explorer/pull/366
.. _#368: https://github.com/explorerhq/sql-explorer/pull/368
.. _#370: https://github.com/explorerhq/sql-explorer/pull/370
.. _#372: https://github.com/explorerhq/sql-explorer/pull/372
.. _#382: https://github.com/explorerhq/sql-explorer/pull/382
.. _#383: https://github.com/explorerhq/sql-explorer/pull/383
.. _#385: https://github.com/explorerhq/sql-explorer/pull/385
.. _#386: https://github.com/explorerhq/sql-explorer/pull/386
.. _#387: https://github.com/explorerhq/sql-explorer/pull/387
.. _#390: https://github.com/explorerhq/sql-explorer/pull/390
.. _#393: https://github.com/explorerhq/sql-explorer/pull/393
.. _#397: https://github.com/explorerhq/sql-explorer/pull/397
.. _#404: https://github.com/explorerhq/sql-explorer/pull/404
.. _#406: https://github.com/explorerhq/sql-explorer/pull/406
.. _#408: https://github.com/explorerhq/sql-explorer/pull/408
.. _#410: https://github.com/explorerhq/sql-explorer/pull/410
.. _#413: https://github.com/explorerhq/sql-explorer/pull/413
.. _#414: https://github.com/explorerhq/sql-explorer/pull/414
.. _#416: https://github.com/explorerhq/sql-explorer/pull/416
.. _#415: https://github.com/explorerhq/sql-explorer/pull/415
.. _#417: https://github.com/explorerhq/sql-explorer/pull/417
.. _#418: https://github.com/explorerhq/sql-explorer/pull/418
.. _#420: https://github.com/explorerhq/sql-explorer/pull/420
.. _#424: https://github.com/explorerhq/sql-explorer/pull/424
.. _#425: https://github.com/explorerhq/sql-explorer/pull/425
.. _#441: https://github.com/explorerhq/sql-explorer/pull/441
.. _#442: https://github.com/explorerhq/sql-explorer/pull/442
.. _#444: https://github.com/explorerhq/sql-explorer/pull/444
.. _#445: https://github.com/explorerhq/sql-explorer/pull/445
.. _#449: https://github.com/explorerhq/sql-explorer/pull/449
.. _#450: https://github.com/explorerhq/sql-explorer/pull/450
.. _#470: https://github.com/explorerhq/sql-explorer/pull/470
.. _#471: https://github.com/explorerhq/sql-explorer/pull/471
.. _#475: https://github.com/explorerhq/sql-explorer/pull/475
.. _#478: https://github.com/explorerhq/sql-explorer/pull/478
.. _#481: https://github.com/explorerhq/sql-explorer/pull/481
.. _#484: https://github.com/explorerhq/sql-explorer/pull/484
.. _#488: https://github.com/explorerhq/sql-explorer/pull/488
.. _#494: https://github.com/explorerhq/sql-explorer/pull/494
.. _#496: https://github.com/explorerhq/sql-explorer/pull/496
.. _#497: https://github.com/explorerhq/sql-explorer/pull/497
.. _#498: https://github.com/explorerhq/sql-explorer/pull/498
.. _#500: https://github.com/explorerhq/sql-explorer/pull/500
.. _#501: https://github.com/explorerhq/sql-explorer/pull/501
.. _#504: https://github.com/explorerhq/sql-explorer/pull/504
.. _#505: https://github.com/explorerhq/sql-explorer/pull/505
.. _#506: https://github.com/explorerhq/sql-explorer/pull/506
.. _#508: https://github.com/explorerhq/sql-explorer/pull/508
.. _#515: https://github.com/explorerhq/sql-explorer/pull/515
.. _#517: https://github.com/explorerhq/sql-explorer/pull/517
.. _#519: https://github.com/explorerhq/sql-explorer/pull/519
.. _#520: https://github.com/explorerhq/sql-explorer/pull/520
.. _#521: https://github.com/explorerhq/sql-explorer/pull/521
.. _#522: https://github.com/explorerhq/sql-explorer/pull/522
.. _#523: https://github.com/explorerhq/sql-explorer/pull/523
.. _#524: https://github.com/explorerhq/sql-explorer/pull/524
.. _#528: https://github.com/explorerhq/sql-explorer/pull/528
.. _#529: https://github.com/explorerhq/sql-explorer/pull/529
.. _#533: https://github.com/explorerhq/sql-explorer/pull/533
.. _#537: https://github.com/explorerhq/sql-explorer/pull/537
.. _#539: https://github.com/explorerhq/sql-explorer/pull/539
.. _#544: https://github.com/explorerhq/sql-explorer/pull/544
.. _#562: https://github.com/explorerhq/sql-explorer/pull/562
.. _#565: https://github.com/explorerhq/sql-explorer/pull/565
.. _#566: https://github.com/explorerhq/sql-explorer/pull/566
.. _#571: https://github.com/explorerhq/sql-explorer/pull/571
.. _#594: https://github.com/explorerhq/sql-explorer/pull/594
.. _#647: https://github.com/explorerhq/sql-explorer/pull/647
.. _#643: https://github.com/explorerhq/sql-explorer/pull/643
.. _#644: https://github.com/explorerhq/sql-explorer/pull/644
.. _#645: https://github.com/explorerhq/sql-explorer/pull/645
.. _#648: https://github.com/explorerhq/sql-explorer/pull/648
.. _#649: https://github.com/explorerhq/sql-explorer/pull/649
.. _#635: https://github.com/explorerhq/sql-explorer/pull/635
.. _#636: https://github.com/explorerhq/sql-explorer/pull/636
.. _#555: https://github.com/explorerhq/sql-explorer/pull/555
.. _#651: https://github.com/explorerhq/sql-explorer/pull/651
.. _#659: https://github.com/explorerhq/sql-explorer/pull/659
.. _#662: https://github.com/explorerhq/sql-explorer/pull/662
.. _#660: https://github.com/explorerhq/sql-explorer/pull/660
.. _#664: https://github.com/explorerhq/sql-explorer/pull/664

.. _#269: https://github.com/explorerhq/sql-explorer/issues/269
.. _#288: https://github.com/explorerhq/sql-explorer/issues/288
.. _#341: https://github.com/explorerhq/sql-explorer/issues/341
.. _#371: https://github.com/explorerhq/sql-explorer/issues/371
.. _#396: https://github.com/explorerhq/sql-explorer/issues/396
.. _#412: https://github.com/explorerhq/sql-explorer/issues/412
.. _#430: https://github.com/explorerhq/sql-explorer/issues/430
.. _#431: https://github.com/explorerhq/sql-explorer/issues/431
.. _#433: https://github.com/explorerhq/sql-explorer/issues/433
.. _#440: https://github.com/explorerhq/sql-explorer/issues/440
.. _#443: https://github.com/explorerhq/sql-explorer/issues/443
.. _#477: https://github.com/explorerhq/sql-explorer/issues/477
.. _#483: https://github.com/explorerhq/sql-explorer/issues/483
.. _#490: https://github.com/explorerhq/sql-explorer/issues/490
.. _#492: https://github.com/explorerhq/sql-explorer/issues/492
.. _#592: https://github.com/explorerhq/sql-explorer/issues/592
.. _#609: https://github.com/explorerhq/sql-explorer/issues/609
.. _#610: https://github.com/explorerhq/sql-explorer/issues/610
.. _#612: https://github.com/explorerhq/sql-explorer/issues/612
.. _#616: https://github.com/explorerhq/sql-explorer/issues/616
.. _#618: https://github.com/explorerhq/sql-explorer/issues/618
.. _#619: https://github.com/explorerhq/sql-explorer/issues/619
.. _#631: https://github.com/explorerhq/sql-explorer/issues/631
.. _#633: https://github.com/explorerhq/sql-explorer/issues/633
.. _#567: https://github.com/explorerhq/sql-explorer/issues/567
.. _#654: https://github.com/explorerhq/sql-explorer/issues/654
.. _#653: https://github.com/explorerhq/sql-explorer/issues/653

.. _furo: https://github.com/pradyunsg/furo
