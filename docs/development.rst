Running Locally (quick start)
-----------------------------

Whether you have cloned the repo, or installed via pip, included is a test_project that you can use to kick the tires.

Run:

``docker compose up``

You can now navigate to 127.0.0.1:8000/explorer/, log in with admin/admin, and begin exploring!

Installing From Source
----------------------

If you want to install SQL Explorer from source (e.g. not from the built PyPi package),
into an existing project, you can do so by cloning the repository and following the usual
:doc:`install` instructions, and then additionally building the front-end dependencies:

::

    nvm install
    nvm use
    npm install
    npm run build

The front-end assets will be built and placed in the /static/ folder
and collected properly by your Django installation during the `collect static`
phase. Copy the /explorer directory into site-packages and you're ready to go.

Tests
-----

Install the dev requirements:

``pip install -r requirements/dev.txt``

And then:

``python manage.py test --settings=explorer.tests.settings``

Or with coverage:

``coverage run --source='.' manage.py test --settings=explorer.tests.settings``
``coverage combine``
``coverage report``
