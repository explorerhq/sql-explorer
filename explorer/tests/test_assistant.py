from explorer.tests.factories import SimpleQueryFactory, QueryLogFactory
from unittest.mock import patch, Mock, MagicMock

import json
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.db import OperationalError
from explorer.app_settings import EXPLORER_DEFAULT_CONNECTION as CONN
from explorer.assistant.utils import sample_rows_from_table, ROW_SAMPLE_SIZE, build_prompt


class TestAssistantViews(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser(
            "admin", "admin@admin.com", "pwd"
        )
        self.client.login(username="admin", password="pwd")
        self.request_data = {
           "sql": "SELECT * FROM explorer_query",
           "connection": CONN,
           "assistant_request": "Test Request"
        }

    @patch("explorer.assistant.utils.openai_client")
    def test_do_modify_query(self, mocked_openai_client):
        from explorer.assistant.views import run_assistant

        # create.return_value should match: resp.choices[0].message
        mocked_openai_client.return_value.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="smart computer"))])
        resp = run_assistant(self.request_data, None)
        self.assertEqual(resp, "smart computer")

    @patch("explorer.assistant.utils.openai_client")
    def test_assistant_help(self, mocked_openai_client):
        mocked_openai_client.return_value.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="smart computer"))])
        resp = self.client.post(reverse("assistant"),
                                data=json.dumps(self.request_data),
                                content_type="application/json")
        self.assertEqual(json.loads(resp.content)["message"], "smart computer")


class TestBuildPrompt(TestCase):

    @patch("explorer.assistant.utils.sample_rows_from_tables", return_value="sample data")
    @patch("explorer.assistant.utils.fits_in_window", return_value=True)
    @patch("explorer.models.ExplorerValue.objects.get_item")
    def test_build_prompt_with_vendor_only(self, mock_get_item, mock_fits_in_window, mock_sample_rows):
        mock_get_item.return_value.value = "system prompt"

        request_data = {
            "connection": "default",
            "assistant_request": "Help me with SQL"
        }
        included_tables = []

        result = build_prompt(request_data, included_tables)
        self.assertIn("## Database Vendor / SQL Flavor is sqlite", result["user"])
        self.assertIn("## User's Request to Assistant ##\n\nHelp me with SQL\n\n", result["user"])
        self.assertEqual(result["system"], "system prompt")

    @patch("explorer.assistant.utils.sample_rows_from_tables", return_value="sample data")
    @patch("explorer.assistant.utils.fits_in_window", return_value=True)
    @patch("explorer.models.ExplorerValue.objects.get_item")
    def test_build_prompt_with_sql(self, mock_get_item, mock_fits_in_window, mock_sample_rows):
        mock_get_item.return_value.value = "system prompt"

        request_data = {
            "connection": "default",
            "sql": "SELECT * FROM table;",
            "assistant_request": "Help me with SQL"
        }
        included_tables = []

        result = build_prompt(request_data, included_tables)
        self.assertIn("## Database Vendor / SQL Flavor is sqlite", result["user"])
        self.assertIn("## Existing SQL ##\n\nSELECT * FROM table;\n\n", result["user"])
        self.assertIn("## User's Request to Assistant ##\n\nHelp me with SQL\n\n", result["user"])
        self.assertEqual(result["system"], "system prompt")

    @patch("explorer.assistant.utils.sample_rows_from_tables", return_value="sample data")
    @patch("explorer.assistant.utils.fits_in_window", return_value=True)
    @patch("explorer.models.ExplorerValue.objects.get_item")
    def test_build_prompt_with_sql_and_error(self, mock_get_item, mock_fits_in_window, mock_sample_rows):
        mock_get_item.return_value.value = "system prompt"

        request_data = {
            "connection": "default",
            "sql": "SELECT * FROM table;",
            "db_error": "Syntax error",
            "assistant_request": "Help me with SQL"
        }
        included_tables = []

        result = build_prompt(request_data, included_tables)
        self.assertIn("## Database Vendor / SQL Flavor is sqlite", result["user"])
        self.assertIn("## Existing SQL ##\n\nSELECT * FROM table;\n\n", result["user"])
        self.assertIn("## Query Error ##\n\nSyntax error\n\n", result["user"])
        self.assertIn("## User's Request to Assistant ##\n\nHelp me with SQL\n\n", result["user"])
        self.assertEqual(result["system"], "system prompt")

    @patch("explorer.assistant.utils.sample_rows_from_tables", return_value="sample data")
    @patch("explorer.assistant.utils.fits_in_window", return_value=True)
    @patch("explorer.models.ExplorerValue.objects.get_item")
    def test_build_prompt_with_extra_tables_fitting_window(self, mock_get_item, mock_fits_in_window, mock_sample_rows):
        mock_get_item.return_value.value = "system prompt"

        request_data = {
            "connection": "default",
            "sql": "SELECT * FROM table;",
            "assistant_request": "Help me with SQL"
        }
        included_tables = ["table1", "table2"]

        result = build_prompt(request_data, included_tables)
        self.assertIn("## Database Vendor / SQL Flavor is sqlite", result["user"])
        self.assertIn("## Existing SQL ##\n\nSELECT * FROM table;\n\n", result["user"])
        self.assertIn("## Table Structure with Sampled Data ##\n\nsample data\n\n", result["user"])
        self.assertIn("## User's Request to Assistant ##\n\nHelp me with SQL\n\n", result["user"])
        self.assertEqual(result["system"], "system prompt")

    @patch("explorer.assistant.utils.sample_rows_from_tables", return_value="sample data")
    @patch("explorer.assistant.utils.fits_in_window", return_value=False)
    @patch("explorer.assistant.utils.tables_from_schema_info", return_value="table structure")
    @patch("explorer.models.ExplorerValue.objects.get_item")
    def test_build_prompt_with_extra_tables_not_fitting_window(self, mock_get_item, mock_tables_from_schema_info,
                                                               mock_fits_in_window, mock_sample_rows):
        mock_get_item.return_value.value = "system prompt"

        request_data = {
            "connection": "default",
            "sql": "SELECT * FROM table;",
            "assistant_request": "Help me with SQL"
        }
        included_tables = ["table1", "table2"]

        result = build_prompt(request_data, included_tables)
        self.assertIn("## Database Vendor / SQL Flavor is sqlite", result["user"])
        self.assertIn("## Existing SQL ##\n\nSELECT * FROM table;\n\n", result["user"])
        self.assertIn("## Table Structure ##\n\ntable structure\n\n", result["user"])
        self.assertIn("## User's Request to Assistant ##\n\nHelp me with SQL\n\n", result["user"])
        self.assertEqual(result["system"], "system prompt")


class TestPromptContext(TestCase):

    def test_retrieves_sample_rows(self):
        SimpleQueryFactory(title="First Query")
        SimpleQueryFactory(title="Second Query")
        SimpleQueryFactory(title="Third Query")
        SimpleQueryFactory(title="Fourth Query")
        ret = sample_rows_from_table(CONN, "explorer_query")
        self.assertEqual(len(ret), ROW_SAMPLE_SIZE+1)  # includes header row

    @patch("explorer.assistant.utils.get_valid_connection")
    def test_truncates_long_strings(self, mock_get_valid_connection):
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_valid_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        long_string = "a" * 600
        mock_cursor.description = [("col1",), ("col2",)]
        mock_cursor.fetchall.return_value = [(long_string, "short string")]

        ret = sample_rows_from_table(CONN, "some_table")
        header, row = ret

        self.assertEqual(header, ["col1", "col2"])
        self.assertEqual(row[0], "a" * 500 + "...")
        self.assertEqual(row[1], "short string")

    @patch("explorer.assistant.utils.get_valid_connection")
    def test_truncates_long_binary_data(self, mock_get_valid_connection):
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_valid_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        long_binary = b"a" * 600
        mock_cursor.description = [("col1",), ("col2",)]
        mock_cursor.fetchall.return_value = [(long_binary, b"short binary")]

        ret = sample_rows_from_table(CONN, "some_table")
        header, row = ret

        self.assertEqual(header, ["col1", "col2"])
        self.assertEqual(row[0], b"a" * 500 + b"...")
        self.assertEqual(row[1], b"short binary")

    @patch("explorer.assistant.utils.get_valid_connection")
    def test_handles_various_data_types(self, mock_get_valid_connection):
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_valid_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.description = [("col1",), ("col2",), ("col3",)]
        mock_cursor.fetchall.return_value = [(123, 45.67, "normal string")]

        ret = sample_rows_from_table(CONN, "some_table")
        header, row = ret

        self.assertEqual(header, ["col1", "col2", "col3"])
        self.assertEqual(row[0], 123)
        self.assertEqual(row[1], 45.67)
        self.assertEqual(row[2], "normal string")

    @patch("explorer.assistant.utils.get_valid_connection")
    def test_handles_operational_error(self, mock_get_valid_connection):
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_valid_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.execute.side_effect = OperationalError("Test OperationalError")

        ret = sample_rows_from_table(CONN, "some_table")

        self.assertEqual(ret, [["Test OperationalError"]])

    def test_format_rows_from_table(self):
        from explorer.assistant.utils import format_rows_from_table
        d = [
            ["col1", "col2"],
            ["val1", "val2"],
        ]
        ret = format_rows_from_table(d)
        self.assertEqual(ret, "col1 | col2\n" + "-" * 50 + "\nval1 | val2\n")

    def test_parsing_tables_from_query(self):
        from explorer.assistant.utils import get_table_names_from_query
        sql = "SELECT * FROM explorer_query"
        ret = get_table_names_from_query(sql)
        self.assertEqual(ret, ["explorer_query"])

    def test_parsing_tables_from_query_bad_sql(self):
        from explorer.assistant.utils import get_table_names_from_query
        sql = "foo"
        ret = get_table_names_from_query(sql)
        self.assertEqual(ret, [])

    def test_schema_info_from_table_names(self):
        from explorer.assistant.utils import tables_from_schema_info
        ret = tables_from_schema_info(CONN, ["explorer_query"])
        expected = [("explorer_query", [
            ("id", "AutoField"),
            ("title", "CharField"),
            ("sql", "TextField"),
            ("description", "TextField"),
            ("created_at", "DateTimeField"),
            ("last_run_date", "DateTimeField"),
            ("created_by_user_id", "IntegerField"),
            ("snapshot", "BooleanField"),
            ("connection", "CharField")])]
        self.assertEqual(ret, expected)


class TestAssistantUtils(TestCase):

    def test_sample_rows_from_tables(self):
        from explorer.assistant.utils import sample_rows_from_tables
        SimpleQueryFactory(title="First Query")
        SimpleQueryFactory(title="Second Query")
        QueryLogFactory()
        ret = sample_rows_from_tables(CONN, ["explorer_query", "explorer_querylog"])
        self.assertTrue("First Query" in ret)
        self.assertTrue("Second Query" in ret)
        self.assertTrue("explorer_querylog" in ret)

    def test_sample_rows_from_tables_no_tables(self):
        from explorer.assistant.utils import sample_rows_from_tables
        SimpleQueryFactory(title="First Query")
        SimpleQueryFactory(title="Second Query")
        ret = sample_rows_from_tables(CONN, [])
        self.assertEqual(ret, "")
