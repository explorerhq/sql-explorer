==========
Change Log
==========

This document records all notable changes to `django-sql-explorer <https://github.com/groveco/django-sql-explorer>`_.
This project adheres to `Semantic Versioning <https://semver.org/>`_.

`unreleased`_ changes
---------------------


`3.0.1`_ (2022-12-16)
---------------------
* `#515`_: Fix for running without optional packages

`3.0.0`_ (2022-12-15)
---------------------
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
---------------------
* `#494`_: Fixes Security hole in blacklist for MySQL (`#490`_)
* `#488`_: docs: Fix a few typos
* `#481`_: feat: Add pie and line chart tabs to query result preview
* `#478`_: feat: Improved templates to make easier to customize (Fix `#477`_)


`2.4.2`_ (2022-08-30)
---------------------
* `#484`_: Added ``DEFAULT_AUTO_FIELD`` (Fix `#483`_)
* `#475`_: Add ``SET`` to blacklisted keywords

`2.4.1`_ (2022-03-10)
---------------------
* `#471`_: Fix extra white space in description and SQL fields.

`2.4.0`_ (2022-02-10)
---------------------
* `#470`_: Upgrade JS/CSS versions.

`2.3.0`_ (2021-07-24)
---------------------
* `#450`_: Added Russian translations.
* `#449`_: Translates expression for duration

`2.2.0`_ (2021-06-14)
---------------------
* Updated docs theme to `furo`_
* `#445`_: Added ``EXPLORER_NO_PERMISSION_VIEW`` setting to allow override of the "no permission" view (Fix `#440`_)
* `#444`_: Updated structure of the settings docs (Fix `#443`_)

`2.1.3`_ (2021-05-14)
---------------------
* `#442`_: ``GET`` params passed to the fullscreen view (Fix `#433`_)
* `#441`_: Include BOM in CSV export (Fix `#430`_)

`2.1.2`_ (2021-01-19)
---------------------
* `#431`_: Fix for hidden SQL panel on a new query

`2.1.1`_ (2021-01-19)
---------------------
Mistake in release

`2.1.0`_ (2021-01-13)
---------------------

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
---------------------

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
---------------------

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
---------------------

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
---------------------

* Fix `#288`_ (incorrect import)


`1.1.0`_ (2017-03-19)
---------------------

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
---------------------

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
---------------------

* Fixed readme issue (.1) and ``setup.py`` issue (.2)

`0.9.1`_ (2016-02-01)
---------------------

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
---------------------

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
---------------------

* Added search functionality to schema view and explorer view (using list.js).
* Python 2.6 compatibility.
* Basic charts via charted (from Medium via charted.co).
* SQL formatting function.
* Token authentication to retrieve csv version of queries.
* Fixed south_migrations packaging issue.
* Refactored front-end and pulled CSS and JS into dedicated files.

`0.6.0`_ (2014-11-05)
---------------------

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
---------------------

Bugfixes

* Created_by_user not getting saved correctly
* Content-disposition .csv issue
* Issue with queries ending in ``...like '%...`` clauses
* Change the way customer user model is referenced

* Pseudo-folders for queries. Use "Foo * Ba1", "Foo * Bar2" for query names and the UI will build a little "Foo" pseudofolder for you in the query list.

`0.5.0`_ (2014-06-06)
---------------------

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
---------------------

* Renaming template blocks to prevent conflicts

`0.4`_ (2014-02-14 `Happy Valentine's Day!`)
--------------------------------------------

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
---------------------

Bug Fixes

* Proper SQL blacklist checks
* Downloading CSV from playground

`0.1`_ (2013-12-29)
-------------------

Initial Release


.. _0.1: https://github.com/groveco/django-sql-explorer/tree/0.1
.. _0.1.1: https://github.com/groveco/django-sql-explorer/compare/0.1...0.1.1
.. _0.2: https://github.com/groveco/django-sql-explorer/compare/0.1.1...0.2
.. _0.3: https://github.com/groveco/django-sql-explorer/compare/0.2...0.3
.. _0.4: https://github.com/groveco/django-sql-explorer/compare/0.3...0.4
.. _0.4.1: https://github.com/groveco/django-sql-explorer/compare/0.4...0.4.1
.. _0.5.0: https://github.com/groveco/django-sql-explorer/compare/0.4.1...0.5.0
.. _0.5.1: https://github.com/groveco/django-sql-explorer/compare/0.5.0...541148e7240e610f01dd0c260969c8d56e96a462
.. _0.6.0: https://github.com/groveco/django-sql-explorer/compare/0.5.0...0.6.0
.. _0.7.0: https://github.com/groveco/django-sql-explorer/compare/0.6.0...0.7.0
.. _0.8.0: https://github.com/groveco/django-sql-explorer/compare/0.7.0...0.8.0
.. _0.9.0: https://github.com/groveco/django-sql-explorer/compare/0.8.0...0.9.0
.. _0.9.1: https://github.com/groveco/django-sql-explorer/compare/0.9.0...0.9.1
.. _0.9.2: https://github.com/groveco/django-sql-explorer/compare/0.9.1...0.9.2
.. _1.0.0: https://github.com/groveco/django-sql-explorer/compare/0.9.2...1.0.0

.. _1.1.0: https://github.com/groveco/django-sql-explorer/compare/1.0.0...1.1.1
.. _1.1.1: https://github.com/groveco/django-sql-explorer/compare/1.1.0...1.1.1
.. _1.1.2: https://github.com/groveco/django-sql-explorer/compare/1.1.1...1.1.2
.. _1.1.3: https://github.com/groveco/django-sql-explorer/compare/1.1.2...1.1.3
.. _2.0.0: https://github.com/groveco/django-sql-explorer/compare/1.1.3...2.0
.. _2.1.0: https://github.com/groveco/django-sql-explorer/compare/2.0...2.1.0
.. _2.1.1: https://github.com/groveco/django-sql-explorer/compare/2.1.0...2.1.1
.. _2.1.2: https://github.com/groveco/django-sql-explorer/compare/2.1.1...2.1.2
.. _2.1.3: https://github.com/groveco/django-sql-explorer/compare/2.1.2...2.1.3
.. _2.2.0: https://github.com/groveco/django-sql-explorer/compare/2.1.3...2.2.0
.. _2.3.0: https://github.com/groveco/django-sql-explorer/compare/2.2.0...2.3.0
.. _2.4.0: https://github.com/groveco/django-sql-explorer/compare/2.3.0...2.4.0
.. _2.4.1: https://github.com/groveco/django-sql-explorer/compare/2.4.0...2.4.1
.. _2.4.2: https://github.com/groveco/django-sql-explorer/compare/2.4.1...2.4.2
.. _2.5.0: https://github.com/groveco/django-sql-explorer/compare/2.4.2...2.5.0
.. _3.0.0: https://github.com/groveco/django-sql-explorer/compare/2.5.0...3.0.0
.. _unreleased: https://github.com/groveco/django-sql-explorer/compare/2.4.2...master

.. _#254: https://github.com/groveco/django-sql-explorer/pull/254
.. _#334: https://github.com/groveco/django-sql-explorer/pull/334
.. _#337: https://github.com/groveco/django-sql-explorer/pull/337
.. _#345: https://github.com/groveco/django-sql-explorer/pull/345
.. _#347: https://github.com/groveco/django-sql-explorer/pull/347
.. _#354: https://github.com/groveco/django-sql-explorer/pull/354
.. _#357: https://github.com/groveco/django-sql-explorer/pull/357
.. _#359: https://github.com/groveco/django-sql-explorer/pull/359
.. _#363: https://github.com/groveco/django-sql-explorer/pull/363
.. _#366: https://github.com/groveco/django-sql-explorer/pull/366
.. _#368: https://github.com/groveco/django-sql-explorer/pull/368
.. _#370: https://github.com/groveco/django-sql-explorer/pull/370
.. _#372: https://github.com/groveco/django-sql-explorer/pull/372
.. _#382: https://github.com/groveco/django-sql-explorer/pull/382
.. _#383: https://github.com/groveco/django-sql-explorer/pull/383
.. _#385: https://github.com/groveco/django-sql-explorer/pull/385
.. _#386: https://github.com/groveco/django-sql-explorer/pull/386
.. _#387: https://github.com/groveco/django-sql-explorer/pull/387
.. _#390: https://github.com/groveco/django-sql-explorer/pull/390
.. _#393: https://github.com/groveco/django-sql-explorer/pull/393
.. _#397: https://github.com/groveco/django-sql-explorer/pull/397
.. _#404: https://github.com/groveco/django-sql-explorer/pull/404
.. _#406: https://github.com/groveco/django-sql-explorer/pull/406
.. _#408: https://github.com/groveco/django-sql-explorer/pull/408
.. _#410: https://github.com/groveco/django-sql-explorer/pull/410
.. _#413: https://github.com/groveco/django-sql-explorer/pull/413
.. _#414: https://github.com/groveco/django-sql-explorer/pull/414
.. _#416: https://github.com/groveco/django-sql-explorer/pull/416
.. _#415: https://github.com/groveco/django-sql-explorer/pull/415
.. _#417: https://github.com/groveco/django-sql-explorer/pull/417
.. _#418: https://github.com/groveco/django-sql-explorer/pull/418
.. _#420: https://github.com/groveco/django-sql-explorer/pull/420
.. _#424: https://github.com/groveco/django-sql-explorer/pull/424
.. _#425: https://github.com/groveco/django-sql-explorer/pull/425
.. _#441: https://github.com/groveco/django-sql-explorer/pull/441
.. _#442: https://github.com/groveco/django-sql-explorer/pull/442
.. _#444: https://github.com/groveco/django-sql-explorer/pull/444
.. _#445: https://github.com/groveco/django-sql-explorer/pull/445
.. _#449: https://github.com/groveco/django-sql-explorer/pull/449
.. _#450: https://github.com/groveco/django-sql-explorer/pull/450
.. _#470: https://github.com/groveco/django-sql-explorer/pull/470
.. _#471: https://github.com/groveco/django-sql-explorer/pull/471
.. _#475: https://github.com/groveco/django-sql-explorer/pull/475
.. _#478: https://github.com/groveco/django-sql-explorer/pull/478
.. _#481: https://github.com/groveco/django-sql-explorer/pull/481
.. _#484: https://github.com/groveco/django-sql-explorer/pull/484
.. _#488: https://github.com/groveco/django-sql-explorer/pull/488
.. _#494: https://github.com/groveco/django-sql-explorer/pull/494
.. _#496: https://github.com/groveco/django-sql-explorer/pull/496
.. _#497: https://github.com/groveco/django-sql-explorer/pull/497
.. _#498: https://github.com/groveco/django-sql-explorer/pull/498
.. _#500: https://github.com/groveco/django-sql-explorer/pull/500
.. _#501: https://github.com/groveco/django-sql-explorer/pull/501
.. _#504: https://github.com/groveco/django-sql-explorer/pull/504
.. _#505: https://github.com/groveco/django-sql-explorer/pull/505
.. _#506: https://github.com/groveco/django-sql-explorer/pull/506
.. _#508: https://github.com/groveco/django-sql-explorer/pull/508
.. _#515: https://github.com/groveco/django-sql-explorer/pull/515

.. _#269: https://github.com/groveco/django-sql-explorer/issues/269
.. _#288: https://github.com/groveco/django-sql-explorer/issues/288
.. _#341: https://github.com/groveco/django-sql-explorer/issues/341
.. _#371: https://github.com/groveco/django-sql-explorer/issues/371
.. _#396: https://github.com/groveco/django-sql-explorer/issues/396
.. _#412: https://github.com/groveco/django-sql-explorer/issues/412
.. _#430: https://github.com/groveco/django-sql-explorer/issues/430
.. _#431: https://github.com/groveco/django-sql-explorer/issues/431
.. _#433: https://github.com/groveco/django-sql-explorer/issues/433
.. _#440: https://github.com/groveco/django-sql-explorer/issues/440
.. _#443: https://github.com/groveco/django-sql-explorer/issues/443
.. _#477: https://github.com/groveco/django-sql-explorer/issues/477
.. _#483: https://github.com/groveco/django-sql-explorer/issues/483
.. _#490: https://github.com/groveco/django-sql-explorer/issues/490
.. _#492: https://github.com/groveco/django-sql-explorer/issues/492

.. _furo: https://github.com/pradyunsg/furo
