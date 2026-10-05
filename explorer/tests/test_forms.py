from django.core.exceptions import ImproperlyConfigured
from django.db.utils import IntegrityError
from django.forms.models import model_to_dict
from django.test import TestCase
from unittest.mock import patch, MagicMock

from explorer.forms import QueryForm
from explorer.ee.db_connections.forms import DatabaseConnectionForm, MISSING_DRIVER
from explorer.tests.factories import SimpleQueryFactory
from explorer.ee.db_connections.utils import default_db_connection_id


class TestFormValidation(TestCase):

    def test_form_is_valid_with_valid_sql(self):
        q = SimpleQueryFactory(sql="select 1;", created_by_user_id=None)
        form = QueryForm(model_to_dict(q))
        self.assertTrue(form.is_valid())

    def test_form_fails_null(self):
        with self.assertRaises(IntegrityError):
            SimpleQueryFactory(sql=None, created_by_user_id=None)

    def test_form_fails_blank(self):
        q = SimpleQueryFactory(sql="", created_by_user_id=None)
        q.params = {}
        form = QueryForm(model_to_dict(q))
        self.assertFalse(form.is_valid())

    def test_form_fails_blacklist(self):
        q = SimpleQueryFactory(sql="delete $$a$$;", created_by_user_id=None)
        q.params = {}
        form = QueryForm(model_to_dict(q))
        self.assertFalse(form.is_valid())


class QueryFormTestCase(TestCase):

    def test_valid_form_submission(self):
        form_data = {
            "title": "Test Query",
            "sql": "SELECT * FROM table",
            "description": "A test query description",
            "snapshot": False,
            "database_connection": str(default_db_connection_id()),
        }

        form = QueryForm(data=form_data)
        self.assertTrue(form.is_valid(), msg=form.errors)
        query = form.save()

        # Verify that the Query instance was created and is correctly linked to the DatabaseConnection
        self.assertEqual(query.database_connection_id, default_db_connection_id())
        self.assertEqual(query.title, form_data["title"])
        self.assertEqual(query.sql, form_data["sql"])

    @patch("explorer.forms.default_db_connection")
    def test_default_connection_first(self, mocked_default_db_connection):
        dbc = MagicMock()
        dbc.id = default_db_connection_id()
        mocked_default_db_connection.return_value = dbc
        self.assertEqual(default_db_connection_id(), QueryForm().connections[0][0])

        dbc = MagicMock()
        dbc.id = 2
        mocked_default_db_connection.return_value = dbc
        self.assertEqual(2, QueryForm().connections[0][0])


class DatabaseConnectionFormTestCase(TestCase):

    def _data(self, engine):
        return {"alias": "conn", "engine": engine, "name": "db", "user": "", "password": "",
                "host": "", "port": "", "extras": ""}

    def test_valid_when_driver_installed(self):
        form = DatabaseConnectionForm(self._data("django.db.backends.sqlite3"))
        self.assertTrue(form.is_valid(), form.errors)

    @patch("explorer.ee.db_connections.models.load_backend")
    def test_invalid_when_driver_missing(self, mock_load):
        mock_load.side_effect = ImproperlyConfigured("Error loading MySQLdb module.")
        form = DatabaseConnectionForm(self._data("django.db.backends.mysql"))
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error("engine", code=MISSING_DRIVER))
        self.assertIn("mysqlclient", form.errors["engine"][0])

    @patch("explorer.ee.db_connections.models.load_backend")
    def test_engine_choices_flag_missing_drivers(self, mock_load):
        def load(engine):
            if engine == "django.db.backends.mysql":
                raise ImproperlyConfigured("Error loading MySQLdb module.")
        mock_load.side_effect = load
        labels = dict(DatabaseConnectionForm().fields["engine"].choices)
        self.assertEqual(labels["django.db.backends.mysql"], "MariaDB (driver not installed)")
        self.assertEqual(labels["django.db.backends.sqlite3"], "SQLite3")
