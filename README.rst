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

`Documentation <https://django-sql-explorer.readthedocs.io/en/latest/>`_

SQL Explorer aims to make the flow of data between people fast,
simple, and confusion-free. It is a Django-based application that you
can add to an existing Django site, or use as a standalone business
intelligence tool.

Quickly write and share SQL queries in a simple, usable SQL editor,
preview the results in the browser, share links, download CSV, JSON,
or Excel files (and even expose queries as API endpoints, if desired),
and keep the information flowing!

Comes with support for multiple connections, to many different SQL
database types, a schema explorer, query history (e.g. lightweight
version control), a basic security model, in-browser pivot tables, and
more.

SQL Explorer values simplicity, intuitive use, unobtrusiveness,
stability, and the principle of least surprise.

Sql Explorer is MIT licensed, and pull requests are welcome.

**A view of a query**

.. image:: https://s3-us-west-1.amazonaws.com/django-sql-explorer/2019_2.png

**Viewing all queries**

.. image:: https://s3-us-west-1.amazonaws.com/django-sql-explorer/2019_querylist.png

**Quick access to DB schema info**

.. image:: https://s3-us-west-1.amazonaws.com/django-sql-explorer/2019_3.png

**Snapshot query results to S3 & download as csv**

.. image:: https://s3-us-west-1.amazonaws.com/django-sql-explorer/2019_snapshots.png

Development
------------

To get started with development, clone the repo, and run the following commands:

.. code-block::

    $ pip install -r requirements/optional.txt django~=4.2
    $ nvm use
    $ npm install
    $ npm run dev &
    $ python manage.py migrate
    $ python manage.py runserver

You can now navigate to 127.0.0.1:8000/ and begin exploring!
