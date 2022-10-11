Install
=======

* Requires Python 3.6 or higher.
* Requires Django 2.2 or higher.

Set up a Django project with the following:

.. code-block:: shell-session

    $ pip install django
    $ django-admin startproject project

More information in the `django tutorial <https://docs.djangoproject.com/en/3.1/intro/tutorial01/>`_.

Install with pip from pypi:

.. code-block:: shell-session

   $ pip install django-sql-explorer

If you would also like to support downloading Excel files install with the dependency using:

.. code-block:: shell-session

   $ pip install django-sql-explorer[xls]

Add to your ``INSTALLED_APPS``, located in the ``settings.py`` file in your project folder:

.. code-block:: python
   :emphasize-lines: 3

    INSTALLED_APPS = (
        ...,
        'explorer',
        ...
    )

Add the following to your urls.py (all Explorer URLs are restricted
via the ``EXPLORER_PERMISSION_VIEW`` and ``EXPLORER_PERMISSION_CHANGE``
settings. See Settings section below for further documentation.):

.. code-block:: python
   :emphasize-lines: 5

    from django.urls import path

    urlpatterns = [
        ...
        path('explorer/', include('explorer.urls')),
        ...
    ]

Configure your settings to something like:

.. code-block:: python

    EXPLORER_CONNECTIONS = { 'Default': 'readonly' }
    EXPLORER_DEFAULT_CONNECTION = 'readonly'

The first setting lists the connections you want to allow Explorer to
use. The keys of the connections dictionary are friendly names to show
Explorer users, and the values are the actual database aliases used in
``settings.DATABASES``. It is highly recommended to setup read-only roles
in your database, add them in your project's ``DATABASES`` setting and
use these read-only connections in the ``EXPLORER_CONNECTIONS``.

If you want to quickly use django-sql-explorer with the existing default
connection **and know what you are doing** (or you are on development), you
can use the following settings:

.. code-block:: python

    EXPLORER_CONNECTIONS = { 'Default': 'default' }
    EXPLORER_DEFAULT_CONNECTION = 'default'

Finally, run migrate to create the tables:

``python manage.py migrate``

You can now browse to https://yoursite/explorer/ and get exploring!

The default behavior when viewing a parameterized query is to autorun the associated
SQL with the default parameter values. This may perform poorly and you may want
a chance for your users to review the parameters before running. If so you may add
the following setting which will allow the user to view the query and adjust any
parameters before hitting "Save & Run"

.. code-block:: python

    EXPLORER_AUTORUN_QUERY_WITH_PARAMS = False

There are a handful of features (snapshots, emailing queries) that
rely on Celery and the dependencies in optional-requirements.txt. If
you have Celery installed, set ``EXPLORER_TASKS_ENABLED=True`` in your
settings.py to enable these features.
