from explorer.app_settings import EXPLORER_CONNECTIONS, EXPLORER_DEFAULT_CONNECTION
from django.db import connections as djcs
from django.core.exceptions import ImproperlyConfigured


if EXPLORER_DEFAULT_CONNECTION not in EXPLORER_CONNECTIONS.values():
    raise ImproperlyConfigured(
        'EXPLORER_DEFAULT_CONNECTION is %s, but that alias is not present in the vaules of EXPLORER_CONNECTIONS'
        % EXPLORER_DEFAULT_CONNECTION)


for name, conn_name in EXPLORER_CONNECTIONS.items():
    if conn_name not in djcs:
        raise ImproperlyConfigured(
            'EXPLORER_CONNECTIONS contains (%s, %s), but %s is not a valid Django DB connection.'
            % (name, conn_name, conn_name))


# We export valid SQL connections here so that consuming code never has to
# deal with django.db.connections directly, and risk accessing a connection
# that hasn't been registered to Explorer.

# Django insists that connections that are created in a thread are only accessed
# by that thread, so here we create a dictionary-like collection of the valid
# connections, but does a 'live' lookup of the connection on each item access.


_connections = {c: c for c in djcs if c in EXPLORER_CONNECTIONS.values()}


class ExplorerConnections(dict):

    def __getitem__(self, item):
        return djcs[item]

connections = ExplorerConnections(_connections)