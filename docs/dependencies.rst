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

============================================================ ======== ================
Name                                                         Version  License
============================================================ ======== ================
`Twitter Boostrap <http://getbootstrap.com/>`_               3.4.1    MIT
`jQuery <http://jquery.com/>`_                               3.6.0    MIT
`jQuery Cookie <https://github.com/carhartl/jquery-cookie>`_ 1.4.1    MIT
`jQuery UI <https://jqueryui.com>`_                          1.13.1   MIT
`Underscore <http://underscorejs.org/>`_                     1.13.2   MIT
`Codemirror <http://codemirror.net/>`_                       5.65.1   MIT
`floatThead <http://mkoryak.github.io/floatThead/>`_         1.4.0    MIT
`list.js <http://listjs.com>`_                               1.2.0    MIT
`pivottable.js <http://nicolas.kruchten.com/pivottable/>`_   2.0.2    MIT
============================================================ ======== ================

- All are served locally, with jQuery UI being a custom build.

pivottable.js relies on jQuery UI but only for the ``Sortable`` method.

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

There is also a test_project that you can use to kick the tires. Just
create a new virtualenv, cd into ``test_project`` and run ``start.sh`` (or
walk through the steps yourself) to get a test instance of the app up
and running.
