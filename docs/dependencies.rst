Dependencies
============

An effort has been made to keep the number of dependencies to a
minimum.

Python
------

=========================================================== ======= ================
Name                                                        Version License
=========================================================== ======= ================
`sqlparse <https://github.com/andialbrecht/sqlparse/>`_     0.4.0   BSD
=========================================================== ======= ================

- sqlparse is used for SQL formatting

**Python - Optional Dependencies**

====================================================================  ===========  =============
Name                                                                    Version      License
====================================================================  ===========  =============
`celery <http://www.celeryproject.org/>`_                              >=3.1,<4      BSD
`django-celery <http://www.celeryproject.org/>`_                       >=3.3.1       BSD
`Factory Boy <https://github.com/rbarrois/factory_boy>`_               >=3.1.0       MIT
`xlsxwriter <http://xlsxwriter.readthedocs.io/>`_                      >=1.3.6       BSD
`boto <https://github.com/boto/boto>`_                                 >=2.49        MIT
====================================================================  ===========  =============

- Factory Boy is required for tests
- celery is required for the 'email' feature, and for snapshots
- boto is required for snapshots
- xlsxwriter is required for Excel export (csv still works fine without it)

JavaScript

Please see package.json for the full list of JavaScript dependencies.

Vite builds a single JS bundle for SQL Explorer. The bundle is larger than ideal, at ~600kb due primarily to CodeMirror and the pivot-table functionality (which, regrettably, requires jQuery UI for it's 'sortable' feature).

The bundle is distributed in the PyPi release (and will be found by collectstatic) or can be built via `npm run build`.

Tests
-----

Factory Boy is needed if you'd like to run the tests, which can you do
easily:

``python manage.py test``

and with coverage:

``coverage run --source='.' manage.py test``

then:

``coverage report``

...97%! Huzzah!

Running Locally
---------------

Included is a test_project that you can use to kick the tires. Just
create a new virtualenv, cd into ``test_project`` and run ``start.sh`` (or
walk through the steps yourself) to get a test instance of the app up
and running.

You can now navigate to 127.0.0.1:8000/ and begin exploring!
