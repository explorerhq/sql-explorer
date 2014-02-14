Django SQL Explorer
===================

Django SQL Explorer is inspired by Stack Exchange's `Data Explorer <http://data.stackexchange.com/stackoverflow/queries>`_ and is designed to make the flow of data between people in your company fast, simple, and confusion-free. Quickly write and share SQL queries in a clean, usable query builder, preview the results in the browser, share links to download CSV files, and keep the information flowing baby!

django-sql-explorer is MIT licensed, and pull requests are welcome!

**A view of a query**

.. image:: http://www.untrod.com/django-sql-explorer/query1.jpg

**Viewing all queries**

.. image:: http://www.untrod.com/django-sql-explorer/query2.5.jpg

**Queries can accept parameters. Neato!**

.. image:: http://www.untrod.com/django-sql-explorer/query3.5.jpg

**Quick access to DB schema info**

.. image:: http://www.untrod.com/django-sql-explorer/query-schema-2.jpg


Features
========

- **Security**
    - Let's not kid ourselves - this tool is all about giving people access to running SQL in production. So if that makes you nervous (and it should) - you've been warned. Explorer makes an effort to not allow terrible things to happen, but be careful! Note there is a setting in the tip (master) to use a different SQL connection than the default django connection. It's recommended you use a read-only database role.
    - Explorer supports two different permission checks for users of the tool. Users passing the EXPLORER_PERMISSION_CHANGE test can create, edit, delete, and execute queries. Users who do not pass this test but pass the EXPLORER_PERMISSION_VIEW test can only execute queries. Other users cannot access any part of Explorer. Both permission groups are set to is_staff by default and can be overridden in your settings file.
    - Enforces a SQL blacklist so destructive queries don't get executed (delete, drop, alter, update etc). This is not bulletproof and it's recommended that you instead configure a read-only database role, but when not possible the blacklist provides reasonable protection.
- **Easy to get started**
    - 100% built on Django's ORM, so works with Postgresql, Mysql, and Sqlite.
    - Zero dependencies other than Django and front-end libraries. More detail below.
    - Just want to get in and write some ad-hoc queries? Go nuts with the Playground area.
- **Looks Reasonably Not Crappy**
    - Thanks to CodeMirror and Bootstrap you might actually enjoy this for querying more than pgadmin or phpmyadmin
- **Parameterized Queries**
    - Use $$foo$$ in your queries and Explorer will build a UI to fill out parameters. When viewing a query like 'SELECT * FROM table WHERE id=$$id$$', Explorer will generate UI for the 'id' parameter.
    - Parameters are stashed in the URL, so you can share links to parameterized queries with colleagues
- **Schema Helper**
    - /explorer/schema/ renders a list of your Django apps' table and column names that you can refer to while writing queries. Apps are excludable from this list so users aren't bogged down in tons of irrelevant tables. See settings documentation below for details.
    - This is available quickly as a sidebar helper while composing queries (see screenshot)
    - Supports many_to_many relations as well
- **Template Columns**
    - Let's say you have a query like 'select id, email from user' and you'd like to quickly drill through to the profile page for each user in the result. You can create a "template" column to do just that.
    - Just set up a template column in your settings file:

    ``EXPLORER_TRANSFORMS = [('user', '<a href="https://yoursite.com/profile/{0}/">{0}</a>')]``

    - And change your query to 'SELECT id AS "user", email FROM user'. Explorer will match the "user" column alias to the transform and merge each cell in that column into the template string. Cool!

- **Django Admin Support**
    - Download multiple queries at once as a zip file through Django's admin interface via a built-in admin action.
- **Meaningful Test Coverage**
    - 95% according to coverage...for what that's worth
    - You can run them yourself! Just install factory_boy and run "manage.py test"

Install
=======

Requires Python 2.7. No Python 3 support...yet.

This has been tested only with Django 1.6, however it should work back to 1.4. Please report an issue if you encounter problems on earlier versions of Django.

Install with pip from github:

``pip install django-sql-explorer``

Add to your installed_apps:

``INSTALLED_APPS = (
...,
'explorer',
...
)``

Add the following to your urls.py (all Explorer URLs are restricted to staff only per default):

``url(r'^explorer/', include('explorer.urls')),``

Run syncdb to create the tables (well...just one table really):

``python manage.py syncdb``

Browse to https://yoursite/explorer/ and get exploring!


Dependencies
============

An effort has been made to require no packages other than Django. However a number of front-end dependencies do exist and are documented below. All front-end dependencies are served from CDNJS.com

====================================================== ======= ================
Name                                                   Version License
====================================================== ======= ================
`Twitter Boostrap <http://getbootstrap.com/>`_         3.0.3   MIT
`jQuery <http://jquery.com/>`_                         2.0.3   MIT
`Underscore <http://underscorejs.org/>`_               1.5.2   MIT
`Codemirror <http://codemirror.net/>`_                 3.19.0  MIT
`floatThead <http://mkoryak.github.io/floatThead/>`_ * 1.2.0   Creative Commons
====================================================== ======= ================

`*` Embedded and minified locally because this is not available on cdnjs

Factory Boy is needed if you'd like to run the tests, which can you do easily:

``python manage.py test``

and with coverage:

``coverage run --source='.' manage.py test explorer``


Settings
========

============================ =============================================================================================================== ================================================================================================================================================
Setting                      Description                                                                                                                                                  Default
============================ =============================================================================================================== ================================================================================================================================================
EXPLORER_SQL_BLACKLIST       Disallowed words in SQL queries to prevent destructive actions.                                                 ('ALTER', 'RENAME ', 'DROP', 'TRUNCATE', 'INSERT INTO', 'UPDATE', 'REPLACE', 'DELETE', 'ALTER', 'CREATE TABLE', 'SCHEMA', 'GRANT', 'OWNER TO')
EXPLORER_SQL_WHITELIST       These phrases are allowed, even though part of the phrase appears in the blacklist.                             ('CREATED', 'DELETED')
EXPLORER_DEFAULT_ROWS        The number of rows to show by default in the preview pane.                                                      100
EXPLORER_SCHEMA_EXCLUDE_APPS Don't show schema for these packages in the schema helper.                                                      ('django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions', 'django.contrib.admin')
EXPLORER_CONNECTION_NAME     The name of the Django database connection to use. Ideally set this to a connection with read only permissions  None  # Which means use the 'default' connection
EXPLORER_PERMISSION_VIEW     Callback to check if the user is allowed to view and execute stored queries                                     lambda u: u.is_staff
EXPLORER_PERMISSION_CHANGE   Callback to check if the user is allowed to add/change/delete queries                                           lambda u: u.is_staff
EXPLORER_TRANSFORMS          List of tuples like [('alias', 'Template for {0}')]. See features section of this doc for more info.            []
============================ =============================================================================================================== ================================================================================================================================================
