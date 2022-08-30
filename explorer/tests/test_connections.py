from django.test import TestCase

from explorer.connections import connections
from explorer.app_settings import EXPLORER_DEFAULT_CONNECTION
from django.db import connections as djcs

from explorer.utils import InvalidExplorerConnectionException


class TestConnections(TestCase):

    def test_only_registered_connections_are_in_connections(self):
        self.assertTrue(EXPLORER_DEFAULT_CONNECTION in connections)
        self.assertNotEqual(len(connections), len([c for c in djcs]))

    def test__can_check_for_connection_existence(self):
        self.assertTrue("SQLite" in connections)
        self.assertFalse("garbage" in connections)

    def test__keys__are_all_aliases(self):
        self.assertEqual({'SQLite', 'Another'}, set(connections.keys()))

    def test__values__are_only_registered_db_connections(self):
        self.assertEqual({'default', 'alt'}, {c.alias for c in connections.values()})

    def test__can_lookup_connection_by_DJCS_name_if_registered(self):
        c = connections['default']
        self.assertEqual(c, djcs['default'])

    def test__cannot_lookup_connection_by_DJCS_name_if_not_registered(self):
        with self.assertRaisesMessage(
            InvalidExplorerConnectionException,
            "Attempted to access connection not_registered which is not a Django DB connection exposed by Explorer"
        ):
            _ = connections['not_registered']

    def test__raises_on_unknown_connection_name(self):
        with self.assertRaisesMessage(
            InvalidExplorerConnectionException,
            'Attempted to access connection garbage, '
            'but that is not a registered Explorer connection.'
        ):
            _ = connections['garbage']
