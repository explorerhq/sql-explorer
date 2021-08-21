import importlib
import logging

from django.db import connections as djcs

from explorer.app_settings import EXPLORER_CONNECTIONS
from explorer.utils import InvalidExplorerConnectionException

logger = logging.getLogger(__name__)


class ExplorerConnections:

    def get(self, item, default=None):
        try:
            return self[item]
        except InvalidExplorerConnectionException:
            return default

    def __getitem__(self, item):
        conn = EXPLORER_CONNECTIONS.get(item)
        if not conn:
            if item in djcs:
                # Original connection handling did lookups by the django names not the explorer
                # alias. To support stored uses of URLs accessing connections by the old name
                # (such as schema), we support the django db connectin name as long as it is
                # mapped by some alias in EXPLORER_CONNECTIONS, so as to prevent access to
                # Django DB connections never meant to be exposed by Explorer
                if item not in EXPLORER_CONNECTIONS.values():
                    raise InvalidExplorerConnectionException(
                        f"Attempted to access connection {item} which is "
                        f"not a Django DB connection exposed by Explorer"
                    )
                logger.info(f"using legacy lookup by django connection name for '{item}'")
                conn = item
            else:
                raise InvalidExplorerConnectionException(
                    f'Attempted to access connection {item}, '
                    f'but that is not a registered Explorer connection.'
                )
        # Django insists that connections that are created in a thread are only accessed
        # by that thread, so we do a 'live' lookup of the connection on each item access.
        return djcs[conn]

    def __contains__(self, item):
        return item in EXPLORER_CONNECTIONS

    def __len__(self):
        return len(EXPLORER_CONNECTIONS)

    def keys(self):
        return EXPLORER_CONNECTIONS.keys()

    def values(self):
        return [self[v] for v in EXPLORER_CONNECTIONS.values()]

    def items(self):
        return [(k, self[v]) for k, v in EXPLORER_CONNECTIONS.items()]


connections = ExplorerConnections()
