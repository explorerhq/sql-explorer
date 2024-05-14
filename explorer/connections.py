from django.db import connections as djcs
from django.db import transaction, DEFAULT_DB_ALIAS

from explorer.ee.db_connections.utils import create_django_style_connection
from explorer import app_settings
from explorer.models import DatabaseConnection

# To support user-configured database connections that can be managed through the Explorer UI, *as well* as the
# 'legacy' connections that are configured in Django's normal settings.DATABASES config, we stitch together the two.

# We allow queries to be associated with either type of connection, seamlessly.

# The approach is to allow users to create connections with approximately the same parameters that a settings.DATABASE
# would expect. We then stitch them together into one list. When Explorer needs to access a connection, it coughs up a
# Django DatabaseWrapper connection in either case (natively, if it's coming from settings.DATABASES, or by taking the
# user-created connection and running it through the create_django_style_connection() function in this file).

# In general, amazingly, this "just works" and the entire application is perfectly happy to use either type as a
# connection. The exception to this is that there are a few bits of code that ultimately (or directly) use the
# django.db.transaction.atomic context manager. For some reason that particular Django innard takes an *alias*, not a
# proper connection. Then it retrieves the connection based on that alias. But of course if we are providing a
# user-created connection alias, Django doesn't find it (because it is looking in settings.DATABASES).

# The solution is to monkey-patch the get_connection function that transaction.atomic uses, to make it aware of the
# user-created connections.


def new_get_connection(using=None):
    if using is None:
        using = DEFAULT_DB_ALIAS
    if using in djcs:
        return djcs[using]
    return create_django_style_connection(DatabaseConnection.objects.get(alias=using))


# Monkey patch
transaction.get_connection = new_get_connection


# We export valid SQL connections here so that consuming code never has to
# deal with django.db.connections directly, and risk accessing a connection
# that hasn't been registered to Explorer.

# Django insists that connections that are created in a thread are only accessed
# by that thread, so here we create a dictionary-like collection of the valid
# connections, but does a 'live' lookup of the connection on each item access.
class ExplorerConnections(dict):

    def __getitem__(self, item):
        if item in djcs:
            return djcs[item]
        else:
            return create_django_style_connection(DatabaseConnection.objects.get(alias=item))


def connections():
    _connections = [c for c in djcs if c in app_settings.EXPLORER_CONNECTIONS.values()]
    db_connections = DatabaseConnection.objects.all()
    _connections += [c.alias for c in db_connections]
    return ExplorerConnections(zip(_connections, _connections))


