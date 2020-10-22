Dependencies
============

An effort has been made to keep the number of dependencies to a
minimum.

*Python*

=========================================================== ======= ================
Name                                                        Version License
=========================================================== ======= ================
`sqlparse <https://github.com/andialbrecht/sqlparse/>`_     0.4.0   BSD
=========================================================== ======= ================

- sqlparse is used for SQL formatting

*Python - Optional Dependencies*

==================================================================== ======= ================
Name                                                                 Version License
==================================================================== ======= ================
`celery <http://www.celeryproject.org/>`_                            3.1     BSD
`django-celery <http://www.celeryproject.org/>`_                     3.1     BSD
`Factory Boy <https://github.com/rbarrois/factory_boy>`_             2.12.0  MIT
`xlsxwriter <http://xlsxwriter.readthedocs.io/>`_                    1.2.1   BSD
`boto <https://github.com/boto/boto>`_                               2.46    MIT
==================================================================== ======= ================

- Factory Boy is required for tests
- celery is required for the 'email' feature, and for snapshots
- boto is required for snapshots
- xlsxwriter is required for Excel export (csv still works fine without it)

*JavaScript*

============================================================ ======== ================
Name                                                         Version  License
============================================================ ======== ================
`Twitter Boostrap <http://getbootstrap.com/>`_               3.3.6    MIT
`jQuery <http://jquery.com/>`_                               2.1.4    MIT
`jQuery Cookie <https://github.com/carhartl/jquery-cookie>`_ 1.4.1    MIT
`jQuery UI <https://jqueryui.com>`_                          1.11.4   MIT
`Underscore <http://underscorejs.org/>`_                     1.7.0    MIT
`Codemirror <http://codemirror.net/>`_                       5.15.2   MIT
`floatThead <http://mkoryak.github.io/floatThead/>`_         1.4.0    MIT
`list.js <http://listjs.com>`_                               1.2.0    MIT
`pivottable.js <http://nicolas.kruchten.com/pivottable/>`_   2.0.2    MIT
============================================================ ======== ================

- All all served from CDNJS except for jQuery UI, which uses a custom
  build, served locally.

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