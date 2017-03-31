from django.conf import settings
from django.db import connections
from django.core.exceptions import ImproperlyConfigured

# The 'correct' configuration for Explorer going forward and for new installs looks like:

# EXPLORER_CONNECTIONS = {
#   'Original Database': 'my_important_database_readonly_connection',
#   'Client Database 2': 'other_database_connection'
# }
# EXPLORER_DEFAULT_CONNECTION = 'my_important_database_readonly_connection'

EXPLORER_CONNECTIONS = getattr(settings, 'EXPLORER_CONNECTIONS', {})
EXPLORER_DEFAULT_CONNECTION = getattr(settings, 'EXPLORER_DEFAULT_CONNECTION', None)

if EXPLORER_DEFAULT_CONNECTION not in EXPLORER_CONNECTIONS.values():
    raise ImproperlyConfigured(
        'EXPLORER_DEFAULT_CONNECTION is %s, but that alias is not present in the vaules of EXPLORER_CONNECTIONS'
        % EXPLORER_DEFAULT_CONNECTION)


for name, conn_name in EXPLORER_CONNECTIONS.items():
    if conn_name not in connections:
        raise ImproperlyConfigured(
            'EXPLORER_CONNECTIONS contains (%s, %s), but %s is not a valid Django DB connection.'
            % (name, conn_name, conn_name))
