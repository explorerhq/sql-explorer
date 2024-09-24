from explorer.tests.factories import SimpleQueryFactory, QueryLogFactory
from unittest.mock import patch, Mock, MagicMock
import unittest
from explorer import app_settings

import json
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import User
from django.db import OperationalError
from explorer.ee.db_connections.utils import default_db_connection
from explorer.ee.db_connections.models import DatabaseConnection
from explorer.assistant.utils import (
    sample_rows_from_table,
    ROW_SAMPLE_SIZE,
    build_prompt,
    get_relevant_few_shots,
    get_relevant_annotation,
    table_schema
)

from explorer.assistant.models import TableDescription
from explorer.models import PromptLog


def conn():
    return default_db_connection().as_django_connection()


@unittest.skipIf(not app_settings.has_assistant(), "assistant not enabled")
class TestAssistantViews(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser(
            "admin", "admin@admin.com", "pwd"
        )
        self.client.login(username="admin", password="pwd")
        self.request_data = {
           "sql": "SELECT * FROM explorer_query",
           "connection_id": 1,
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


@unittest.skipIf(not app_settings.has_assistant(), "assistant not enabled")
class TestBuildPrompt(TestCase):

    @patch("explorer.models.ExplorerValue.objects.get_item")
    def test_build_prompt_with_vendor_only(self, mock_get_item):
        mock_get_item.return_value.value = "system prompt"
        result = build_prompt(default_db_connection(),
                              "Help me with SQL", [], sql="SELECT * FROM table;")
        self.assertIn("sqlite", result["system"])

    @patch("explorer.assistant.utils.sample_rows_from_table", return_value="sample data")
    @patch("explorer.assistant.utils.table_schema", return_value=[])
    @patch("explorer.models.ExplorerValue.objects.get_item")
    def test_build_prompt_with_sql_and_annotation(self, mock_get_item, mock_table_schema, mock_sample_rows):
        mock_get_item.return_value.value = "system prompt"

        included_tables = ["foo"]
        td = TableDescription(database_connection=default_db_connection(), table_name="foo", description="annotated")
        td.save()

        result = build_prompt(default_db_connection(),
                              "Help me with SQL", included_tables, sql="SELECT * FROM table;")
        self.assertIn("Usage Notes:\nannotated", result["user"])

    @patch("explorer.assistant.utils.sample_rows_from_table", return_value="sample data")
    @patch("explorer.assistant.utils.table_schema", return_value=[])
    @patch("explorer.models.ExplorerValue.objects.get_item")
    def test_build_prompt_with_few_shot(self, mock_get_item, mock_table_schema, mock_sample_rows):
        mock_get_item.return_value.value = "system prompt"

        included_tables = ["magic"]
        SimpleQueryFactory(title="Few shot", description="the quick brown fox", sql="select 'magic value';",
                           few_shot=True)

        result = build_prompt(default_db_connection(),
                              "Help me with SQL", included_tables, sql="SELECT * FROM table;")
        self.assertIn("Relevant example queries", result["user"])
        self.assertIn("magic value", result["user"])

    @patch("explorer.assistant.utils.sample_rows_from_table", return_value="sample data")
    @patch("explorer.models.ExplorerValue.objects.get_item")
    def test_build_prompt_with_sql_and_error(self, mock_get_item, mock_sample_rows):
        mock_get_item.return_value.value = "system prompt"

        included_tables = []

        result = build_prompt(default_db_connection(),
                              "Help me with SQL", included_tables,
                              "Syntax error", "SELECT * FROM table;")
        self.assertIn("## Existing User-Written SQL ##\nSELECT * FROM table;", result["user"])
        self.assertIn("## Query Error ##\nSyntax error\n", result["user"])
        self.assertIn("## User's Request to Assistant ##\nHelp me with SQL", result["user"])
        self.assertIn("system prompt", result["system"])

    @patch("explorer.models.ExplorerValue.objects.get_item")
    def test_build_prompt_with_extra_tables_fitting_window(self, mock_get_item):
        mock_get_item.return_value.value = "system prompt"

        included_tables = ["explorer_query"]
        SimpleQueryFactory()

        result = build_prompt(default_db_connection(), "Help me with SQL",
                              included_tables, sql="SELECT * FROM table;")
        self.assertIn("## Information for Table 'explorer_query' ##", result["user"])
        self.assertIn("Sample rows:\nid | title", result["user"])


@unittest.skipIf(not app_settings.has_assistant(), "assistant not enabled")
class TestPromptContext(TestCase):

    def test_retrieves_sample_rows(self):
        SimpleQueryFactory(title="First Query")
        SimpleQueryFactory(title="Second Query")
        SimpleQueryFactory(title="Third Query")
        SimpleQueryFactory(title="Fourth Query")
        ret = sample_rows_from_table(conn(), "explorer_query")
        self.assertEqual(len(ret), ROW_SAMPLE_SIZE+1)  # includes header row

    def test_truncates_long_strings(self):
        c = MagicMock
        mock_cursor = MagicMock()
        long_string = "a" * 600
        mock_cursor.description = [("col1",), ("col2",)]
        mock_cursor.fetchall.return_value = [(long_string, "short string")]
        c.cursor = MagicMock()
        c.cursor.return_value = mock_cursor

        ret = sample_rows_from_table(c, "some_table")
        header, row = ret

        self.assertEqual(header, ["col1", "col2"])
        self.assertEqual(row[0], "a" * 200 + "...")
        self.assertEqual(row[1], "short string")

    def test_binary_data(self):
        long_binary = b"a" * 600

        # Mock database connection and cursor
        c = MagicMock
        mock_cursor = MagicMock()
        mock_cursor.description = [("col1",), ("col2",)]
        mock_cursor.fetchall.return_value = [(long_binary, b"short binary")]
        c.cursor = MagicMock()
        c.cursor.return_value = mock_cursor

        ret = sample_rows_from_table(c, "some_table")
        header, row = ret

        self.assertEqual(header, ["col1", "col2"])
        self.assertEqual(row[0], "<binary_data>")
        self.assertEqual(row[1], "<binary_data>")

    def test_handles_various_data_types(self):
        # Mock database connection and cursor
        c = MagicMock
        mock_cursor = MagicMock()
        mock_cursor.description = [("col1",), ("col2",), ("col3",)]
        mock_cursor.fetchall.return_value = [(123, 45.67, "normal string")]
        c.cursor = MagicMock()
        c.cursor.return_value = mock_cursor

        ret = sample_rows_from_table(c, "some_table")
        header, row = ret

        self.assertEqual(header, ["col1", "col2", "col3"])
        self.assertEqual(row[0], 123)
        self.assertEqual(row[1], 45.67)
        self.assertEqual(row[2], "normal string")

    def test_handles_operational_error(self):
        c = MagicMock
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = OperationalError("Test OperationalError")
        c.cursor = MagicMock()
        c.cursor.return_value = mock_cursor

        ret = sample_rows_from_table(c, "some_table")

        self.assertEqual(ret, [["Test OperationalError"]])

    def test_format_rows_from_table(self):
        from explorer.assistant.utils import format_rows_from_table
        d = [
            ["col1", "col2"],
            ["val1", "val2"],
        ]
        ret = format_rows_from_table(d)
        self.assertEqual(ret, "col1 | col2\nval1 | val2")

    def test_schema_info_from_table_names(self):
        ret = table_schema(default_db_connection(), "explorer_query")
        expected = [
            ("id", "AutoField"),
            ("title", "CharField"),
            ("sql", "TextField"),
            ("description", "TextField"),
            ("created_at", "DateTimeField"),
            ("last_run_date", "DateTimeField"),
            ("created_by_user_id", "IntegerField"),
            ("snapshot", "BooleanField"),
            ("connection", "CharField"),
            ("database_connection_id", "IntegerField"),
            ("few_shot", "BooleanField")]
        self.assertEqual(ret, expected)

    def test_schema_info_from_table_names_case_invariant(self):
        ret = table_schema(default_db_connection(), "EXPLORER_QUERY")
        expected = [
            ("id", "AutoField"),
            ("title", "CharField"),
            ("sql", "TextField"),
            ("description", "TextField"),
            ("created_at", "DateTimeField"),
            ("last_run_date", "DateTimeField"),
            ("created_by_user_id", "IntegerField"),
            ("snapshot", "BooleanField"),
            ("connection", "CharField"),
            ("database_connection_id", "IntegerField"),
            ("few_shot", "BooleanField")]
        self.assertEqual(ret, expected)


@unittest.skipIf(not app_settings.has_assistant(), "assistant not enabled")
class TestAssistantUtils(TestCase):

    def test_sample_rows_from_table(self):
        from explorer.assistant.utils import sample_rows_from_table, format_rows_from_table
        SimpleQueryFactory(title="First Query")
        SimpleQueryFactory(title="Second Query")
        QueryLogFactory()
        ret = sample_rows_from_table(conn(), "explorer_query")
        self.assertEqual(len(ret), ROW_SAMPLE_SIZE)
        ret = format_rows_from_table(ret)
        self.assertTrue("First Query" in ret)
        self.assertTrue("Second Query" in ret)

    def test_sample_rows_from_tables_no_table_match(self):
        from explorer.assistant.utils import sample_rows_from_table
        SimpleQueryFactory(title="First Query")
        SimpleQueryFactory(title="Second Query")
        ret = sample_rows_from_table(conn(), "banana")
        self.assertEqual(ret, [["no such table: banana"]])

    def test_relevant_few_shots(self):
        relevant_q1 = SimpleQueryFactory(sql="select * from relevant_table", few_shot=True)
        relevant_q2 = SimpleQueryFactory(sql="select * from conn.RELEVANT_TABLE limit 10", few_shot=True)
        irrelevant_q2 = SimpleQueryFactory(sql="select * from conn.RELEVANT_TABLE limit 10", few_shot=False)
        relevant_q3 = SimpleQueryFactory(sql="select * from conn.another_good_table limit 10", few_shot=True)
        irrelevant_q1 = SimpleQueryFactory(sql="select * from irrelevant_table")
        included_tables = ["relevant_table", "ANOTHER_GOOD_TABLE"]
        res = get_relevant_few_shots(relevant_q1.database_connection, included_tables)
        res_ids = [td.id for td in res]
        self.assertIn(relevant_q1.id, res_ids)
        self.assertIn(relevant_q2.id, res_ids)
        self.assertIn(relevant_q3.id, res_ids)
        self.assertNotIn(irrelevant_q1.id, res_ids)
        self.assertNotIn(irrelevant_q2.id, res_ids)

    def test_get_relevant_annotations(self):

        relevant1 = TableDescription(
            database_connection=default_db_connection(),
            table_name="fruit"
        )
        relevant2 = TableDescription(
            database_connection=default_db_connection(),
            table_name="Vegetables"
        )
        irrelevant = TableDescription(
            database_connection=default_db_connection(),
            table_name="animals"
        )
        relevant1.save()
        relevant2.save()
        irrelevant.save()
        res1 = get_relevant_annotation(default_db_connection(), "Fruit")
        self.assertEqual(relevant1.id, res1.id)
        res2 = get_relevant_annotation(default_db_connection(), "vegetables")
        self.assertEqual(relevant2.id, res2.id)


class TestAssistantHistoryApiView(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser(
            "admin", "admin@admin.com", "pwd"
        )
        self.client.login(username="admin", password="pwd")

    def test_assistant_history_api_view(self):
        # Create some PromptLogs
        connection = default_db_connection()
        PromptLog.objects.create(
            run_by_user=self.user,
            database_connection=connection,
            user_request="Test request 1",
            response="Test response 1",
            run_at=timezone.now()
        )
        PromptLog.objects.create(
            run_by_user=self.user,
            database_connection=connection,
            user_request="Test request 2",
            response="Test response 2",
            run_at=timezone.now()
        )

        # Make a POST request to the API
        url = reverse("assistant_history")
        data = {
            "connection_id": connection.id
        }
        response = self.client.post(url, data=json.dumps(data), content_type="application/json")

        # Check the response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertIn("logs", response_data)
        self.assertEqual(len(response_data["logs"]), 2)
        self.assertEqual(response_data["logs"][0]["user_request"], "Test request 2")
        self.assertEqual(response_data["logs"][0]["response"], "Test response 2")
        self.assertEqual(response_data["logs"][1]["user_request"], "Test request 1")
        self.assertEqual(response_data["logs"][1]["response"], "Test response 1")

    def test_assistant_history_api_view_invalid_json(self):
        url = reverse("assistant_history")
        response = self.client.post(url, data="invalid json", content_type="application/json")
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["status"], "error")
        self.assertEqual(response_data["message"], "Invalid JSON")

    def test_assistant_history_api_view_no_logs(self):
        connection = default_db_connection()
        url = reverse("assistant_history")
        data = {
            "connection_id": connection.id
        }
        response = self.client.post(url, data=json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertIn("logs", response_data)
        self.assertEqual(len(response_data["logs"]), 0)

    def test_assistant_history_api_view_filtered_results(self):
        # Create two users
        user1 = self.user
        user2 = User.objects.create_superuser(
            "admin2", "admin2@admin.com", "pwd"
        )

        # Create two database connections
        connection1 = default_db_connection()
        connection2 = DatabaseConnection.objects.create(
            alias="test_connection",
            engine="django.db.backends.sqlite3",
            name=":memory:"
        )

        # Create prompt logs for both users and connections
        PromptLog.objects.create(
            run_by_user=user1,
            database_connection=connection1,
            user_request="User1 Connection1 request",
            response="User1 Connection1 response",
            run_at=timezone.now()
        )
        PromptLog.objects.create(
            run_by_user=user1,
            database_connection=connection2,
            user_request="User1 Connection2 request",
            response="User1 Connection2 response",
            run_at=timezone.now()
        )
        PromptLog.objects.create(
            run_by_user=user2,
            database_connection=connection1,
            user_request="User2 Connection1 request",
            response="User2 Connection1 response",
            run_at=timezone.now()
        )

        # Make a POST request to the API as user1
        url = reverse("assistant_history")
        data = {
            "connection_id": connection1.id
        }
        response = self.client.post(url, data=json.dumps(data), content_type="application/json")

        # Check the response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertIn("logs", response_data)
        self.assertEqual(len(response_data["logs"]), 1)
        self.assertEqual(response_data["logs"][0]["user_request"], "User1 Connection1 request")
        self.assertEqual(response_data["logs"][0]["response"], "User1 Connection1 response")

        # Now test with user2
        self.client.logout()
        self.client.login(username="admin2", password="pwd")

        response = self.client.post(url, data=json.dumps(data), content_type="application/json")

        # Check the response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertIn("logs", response_data)
        self.assertEqual(len(response_data["logs"]), 1)
        self.assertEqual(response_data["logs"][0]["user_request"], "User2 Connection1 request")
        self.assertEqual(response_data["logs"][0]["response"], "User2 Connection1 response")
