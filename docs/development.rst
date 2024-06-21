Running Locally (quick start)
-----------------------------

Included is a test_project that you can use to kick the tires. Just
create a new virtualenv, cd into ``test_project`` and run ``start.sh`` (or
walk through the steps yourself) to get a test instance of the app up
and running.

You can now navigate to 127.0.0.1:8000/explorer/ and begin exploring!

Installing From Source
----------------------

If you are installing SQL Explorer from source (by cloning the repository),
you may want to first look at simply running test_project/start.sh.

If you want to install SQL Explorer from source, into an existing project,
you can do so by cloning the repository and following the usual
:doc:`development` instructions, and then additionally building the front-end
dependencies:

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

Factory Boy is needed if you'd like to run the tests. They can be run with:

``python manage.py test --settings=tests.settings``

and with coverage:

``coverage run --source='.' manage.py test --settings=tests.settings``
``coverage combine``
``coverage report``

Running Celery
--------------

To run tests with Celery enabled, you will need to install Redis and Celery.
::

    brew install redis
    pip install celery
    pip install redis

Then run the redis server and the celery worker. A good way of doing it is:
::

    screen -d -S 'redis' -m redis-server
    screen -d -S 'celery' -m celery -A test_project worker

Finally, set ``EXPLORER_TASKS_ENABLED`` to True in tests.settings and run the tests.
