from io import StringIO

from django.test import TestCase
from django.core.management import call_command


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
