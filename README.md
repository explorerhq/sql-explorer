Django SQL Explorer
==================

Django SQL Explorer is inspired by the Data Explorer tool from Stack Exchange and is designed to make the flow of data between people in your company fast, simple, and confusion-free. Quickly write and share SQL queries in a clean, usable query builder, preview the results in the browser, share links to download CSV files, and keep the information flowing baby!

django-sql-explorer is MIT licensed, and pull requests are welcome!


Requirements & Installation
===========================

Django 1.5+ (though this has only been tested on 1.6...it should work on 1.5 and probably even earlier)
Any database backend that Django supports


Dependencies
============

All front-end dependencies are served from CDNJS.com

Name | Version | License
--- | --- | ---
Twitter Boostrap CSS | |
jQuery | |
Underscore | |
Codemirror | |
FloatThead* | |
FactoryBoy (for tests) | |


* Served locally because it is not available on CDNJS


Install
=======

Clone and add to your installed_apps:

    INSTALLED_APPS = (
      ...
      'explorer',
      ...
    )

Add the following to your urls.py:

    url(r'^explorer/', include('explorer.urls')),

Run syncdb and you're off to the races. Navigate to /explorer/ and create your first query!

Note that all Explorer URLs are restricted to staff only.


Settings
========

Settings names and defaults are below

EXPLORER_SQL_BLACKLIST = getattr(settings, 'EXPLORER_SQL_BLACKLIST', ('ALTER', 'RENAME ', 'DROP', 'TRUNCATE', 'INSERT INTO', 'UPDATE', 'REPLACE', 'DELETE'))

EXPLORER_SQL_WHITELIST = getattr(settings, 'EXPLORER_SQL_WHITELIST', ('DROP FUNCTION', 'REPLACE FUNCTION', 'DROP VIEW', 'REPLACE VIEW', 'CREATED', 'DELETED'))

EXPLORER_DEFAULT_ROWS = getattr(settings, 'EXPLORER_DEFAULT_ROWS', 100)

EXPLORER_SCHEMA_EXCLUDE_APPS = getattr(settings, 'EXPLORER_SCHEMA_EXCLUDE_APPS', ('',))


Features
========

- SQL blacklist so destructive queries don't get executed (delete, drop, etc). This is not bulletproof and it's recommended that you instead configure a read-only database role, but when not possible the blacklist provides reasonable protection.
- Playground! Just want to get in and write some ad-hoc queries? Go nuts!
- Schema helper - /explorer/schema/ will dump a list of your Django apps' table and column names that you can refer to while writing queries.


