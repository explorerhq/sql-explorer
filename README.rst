.. image:: https://readthedocs.org/projects/django-sql-explorer/badge/?version=latest
   :target: https://django-sql-explorer.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

.. image:: http://img.shields.io/pypi/v/django-sql-explorer.svg?style=flat-square
    :target: https://pypi.python.org/pypi/django-sql-explorer/
    :alt: Latest Version

.. image:: http://img.shields.io/pypi/dm/django-sql-explorer.svg?style=flat-square
    :target: https://pypi.python.org/pypi/django-sql-explorer/
    :alt: Downloads

.. image:: http://img.shields.io/pypi/l/django-sql-explorer.svg?style=flat-square
    :target: https://pypi.python.org/pypi/django-sql-explorer/
    :alt: License

SQL Explorer
============

* `Live Demo <https://demo.sqlexplorer.io/>`_

* `Documentation <https://django-sql-explorer.readthedocs.io/en/latest/>`_

* `Website <https://www.sqlexplorer.io/>`_

SQL Explorer aims to make the flow of data between people fast,
simple, and confusion-free. It is a Django-based application that you
can add to an existing Django site, or use as a standalone business
intelligence tool. It will happily connect to any SQL database that
`Django supports <https://docs.djangoproject.com/en/5.0/ref/databases/>`_.

Quickly write and share SQL queries in a simple, usable SQL editor,
view the results in the browser, and keep the information flowing!

Add an OpenAI (or other provider) API key and get an LLM-powered
SQL assistant that can help write and debug queries. The assistant
will automatically add relevant context and schema into the underlying
LLM prompt.

SQL Explorer values simplicity, intuitive use, unobtrusiveness,
stability, and the principle of least surprise. The project is MIT
licensed, and pull requests are welcome.

Some key features include:

- Support for multiple connections
- AI-powered SQL assistant
- Quick access to schema information to make querying easier
  (including autocomplete)
- In-browser pivot tables (which can also be shared via URLs)
- Ability to snapshot queries on a regular schedule, capturing changing
  data
- Query history and logs
- Quick in-browser statistics, pivot tables, and scatter-plots (saving
  a trip to Excel for simple analyses)
- Basic code-completion in the SQL editor
- Parameterized queries that automatically generate a friendly UI for
  users who don't know SQL
- A playground area for quickly running ad-hoc queries
- Send query results via email
- Saved queries can be exposed as a quick-n-dirty JSON API if desired
- ...and more!

Screenshots
-----------

**Writing a query and viewing the schema helper**

.. image:: https://sql-explorer.s3.amazonaws.com/5.0-query-with-schema.png

**Using the SQL AI Assistant**

.. image:: https://sql-explorer.s3.amazonaws.com/5.0-assistant.png

**Viewing all queries**

.. image:: https://sql-explorer.s3.amazonaws.com/5.0-query-list.png

**Query results w/ stats summary**

.. image:: https://sql-explorer.s3.amazonaws.com/5.0-query-results.png

**Pivot in browser**

.. image:: https://sql-explorer.s3.amazonaws.com/5.0-pivot.png

**View logs**

.. image:: https://sql-explorer.s3.amazonaws.com/5.0-querylogs.png

Development
------------

Included is a test_project that you can use to kick the tires. Just
create a new virtualenv, cd into ``test_project`` and run ``start.sh`` (or
walk through the steps yourself) to get a test instance of the app up
and running.

You can now navigate to 127.0.0.1:8000/explorer/ and begin exploring!
