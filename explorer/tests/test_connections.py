from importlib import reload
from django.test import TestCase
from django.db import transaction
from unittest.mock import patch
from explorer.models import DatabaseConnection
from explorer import connections


class ExplorerConnectionsTests(TestCase):

    def test_a_new_get_connection_from_user_created(self):
        # Create a proper DatabaseConnection object
        DatabaseConnection.objects.create(
            alias="user_db",
            name="User Database",
            engine="django.db.backends.sqlite3",
            host="",
            port="",
            user="",
            password="",
        )

        conn = connections.new_get_connection("user_db")
        self.assertEqual(conn.settings_dict["NAME"], "User Database")
        DatabaseConnection.objects.all().delete()

    def test_monkey_patch_transaction_get_connection(self):
        original_get_connection = transaction.get_connection

        reload(connections)  # Reload the module to apply the patch
        self.assertEqual(transaction.get_connection, connections.new_get_connection)

        # Restore original state
        transaction.get_connection = original_get_connection


class ConnectionsBlendingTests(TestCase):

    def setUp(self):
        DatabaseConnection.objects.all().delete()

    @patch("explorer.connections.app_settings")
    def test_connections_blended_when_enabled(self, mocked_app_settings):
        mocked_app_settings.EXPLORER_CONNECTIONS = {"default": "default", "alt": "alt"}
        DatabaseConnection.objects.create(
            alias="user_db1",
            name="User Database",
            engine="django.db.backends.sqlite3",
            host="",
            port="",
            user="",
            password="",
        )

        DatabaseConnection.objects.create(
            alias="user_db2",
            name="User Database",
            engine="django.db.backends.sqlite3",
            host="",
            port="",
            user="",
            password="",
        )

        conn_dict = connections.connections()
        self.assertIn("default", conn_dict)
        self.assertIn("alt", conn_dict)
        self.assertIn("user_db1", conn_dict)
        self.assertIn("user_db2", conn_dict)
        self.assertEqual(len(conn_dict), 4)

