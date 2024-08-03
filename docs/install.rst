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

Take a look at available ``extras``

Add to your ``INSTALLED_APPS``, located in the ``settings.py`` file in your project folder:

..  code-block:: python
    :emphasize-lines: 3

    INSTALLED_APPS = (
        'explorer',
    )

Add the following to your urls.py (all Explorer URLs are restricted
via the ``EXPLORER_PERMISSION_VIEW`` and ``EXPLORER_PERMISSION_CHANGE``
settings. See Settings section below for further documentation.):

..  code-block:: python
    :emphasize-lines: 5

    from django.urls import path, include

    urlpatterns = [
        path('explorer/', include('explorer.urls')),
    ]

Run migrate to create the tables:

``python manage.py migrate``

Create a superuser:

``python manage.py createsuperuser``

And run the server:

``python manage.py runserver``

You can now browse to http://127.0.0.1:8000/explorer/. Add a database connection at /explorer/connections/new/, and you
are ready to start exploring! If you have a database in your settings.DATABASES you would like to query, you can create
a connection with the same alias and name and set the Engine to "Django Database".

Note that Explorer expects STATIC_URL to be set appropriately. This isn't a problem
with vanilla Django setups, but if you are using e.g. Django Storages with S3, you
must set your STATIC_URL to point to your S3 bucket (e.g. s3_bucket_url + '/static/')

AI SQL Assistant
----------------
To enable AI features, you must install the OpenAI SDK and Tiktoken library from
requirements/optional.txt. By default the Assistant is configured to use OpenAI and
the `gpt-4-0125-preview` model. To use those settings, set an OpenAI API token in
your project's settings.py file:

``EXPLORER_AI_API_KEY = 'your_openai_api_key'``

Or, more likely:

``EXPLORER_AI_API_KEY = os.environ.get("OPENAI_API_KEY")``

If you would prefer to use a different provider and/or different model, you can
also override the AI API URL root and default model. For example, this would configure
the Assistant to use OpenRouter and Mixtral 8x7B Instruct:

..  code-block:: python
    :emphasize-lines: 5

    EXPLORER_ASSISTANT_MODEL = {"name": "mistralai/mixtral-8x7b-instruct:nitro",
                                "max_tokens": 32768})
    EXPLORER_ASSISTANT_BASE_URL = "https://openrouter.ai/api/v1"
    EXPLORER_AI_API_KEY = os.environ.get("OPENROUTER_API_KEY")

Other Parameters
----------------

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

Because the front-end assets must be built, installing SQL Explorer via pip
from github is not supported. The package will be installed, but the front-end
assets will be missing and will not be able to be built, as the necessary
configuration files are not included when github builds the wheel for pip.

To run from source, clone the repository and follow the :doc:`development`
instructions.
