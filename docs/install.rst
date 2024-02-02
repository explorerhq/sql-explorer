Install
=======

* Requires Python 3.10 or higher.
* Requires Django 3.2 or higher.

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

..  code-block:: python
    :emphasize-lines: 3

    INSTALLED_APPS = (
        'explorer',
    )

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

Add the following to your urls.py (all Explorer URLs are restricted
via the ``EXPLORER_PERMISSION_VIEW`` and ``EXPLORER_PERMISSION_CHANGE``
settings. See Settings section below for further documentation.):

..  code-block:: python
    :emphasize-lines: 5

    from django.urls import path, include

    urlpatterns = [
        path('explorer/', include('explorer.urls')),
    ]

If you want to quickly use django-sql-explorer with the existing default
connection **and know what you are doing** (or you are on development), you
can use the following settings:

.. code-block:: python

    EXPLORER_CONNECTIONS = { 'Default': 'default' }
    EXPLORER_DEFAULT_CONNECTION = 'default'

Run migrate to create the tables:

``python manage.py migrate``

Create a superuser:

``python manage.py createsuperuser``

And run the server:

``python manage.py runserver``

You can now browse to http://127.0.0.1:8000/explorer/ and get exploring!

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

Installing From Source
----------------------

If you are installing SQL Explorer from source (by cloning the repository),
you may want to first look at simply running test_project/start.sh.

If you want to install it into an existing project, you can do so by following
the instructions above, and additionally building the front-end dependencies.

After cloning, simply run:

::

    nvm install
    nvm use
    npm install
    npm run build

The front-end assets will be built and placed in the /static/ folder
and collected properly by your Django installation during the `collect static`
phase. Copy the /explorer directory into site-packages and you're ready to go.

And frankly, as long as you have a reasonably modern version of Node and NPM
installed, you can probably skip the nvm steps.

Because the front-end assets must be built, installing SQL Explorer via pip
from github is not supported. The package will be installed, but the front-end
assets will be missing and will not be able to be built, as the necessary
configuration files are not included when github builds the wheel for pip.
