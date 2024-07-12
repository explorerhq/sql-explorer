from unittest.mock import patch
from io import StringIO

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from django.core.management import call_command
from explorer.apps import _validate_connections


class TestApps(TestCase):

    @patch("explorer.apps._get_default")
    def test_validates_default_connections(self, mocked_connection):
        mocked_connection.return_value = "garbage"
        self.assertRaises(ImproperlyConfigured, _validate_connections)

    @patch("explorer.apps._get_explorer_connections")
    def test_validates_all_connections(self, mocked_connections):
        mocked_connections.return_value = {"garbage1": "in", "garbage2": "out"}
        self.assertRaises(ImproperlyConfigured, _validate_connections)


class PendingMigrationsTests(TestCase):

    def test_no_pending_migrations(self):
        out = StringIO()
        try:
            call_command(
                "makemigrations",
                "--check",
                stdout=out,
                stderr=StringIO(),
            )
        except SystemExit:  # noqa
            self.fail("Pending migrations:\n" + out.getvalue())
