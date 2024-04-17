from explorer.tests.factories import SimpleQueryFactory
from unittest.mock import patch, Mock
import unittest

import json
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from explorer.app_settings import EXPLORER_DEFAULT_CONNECTION as CONN
from explorer import app_settings


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

    @unittest.skipIf(not app_settings.EXPLORER_AI_API_KEY, "assistant not enabled")
    @patch("explorer.assistant.utils.openai_client")
    def test_do_modify_query(self, mocked_openai_client):
        from explorer.assistant.views import run_assistant

        # create.return_value should match: resp.choices[0].message
        mocked_openai_client.return_value.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="smart computer"))])
        resp = run_assistant(self.request_data, None)
        self.assertEqual(resp, "smart computer")

    @unittest.skipIf(not app_settings.EXPLORER_AI_API_KEY, "assistant not enabled")
    def test_assistant_help(self):
        resp = self.client.post(reverse("assistant"),
                                data=json.dumps(self.request_data),
                                content_type="application/json")
        self.assertIsNone(json.loads(resp.content)["message"])


class TestPromptContext(TestCase):

    def test_retrieves_sample_rows(self):
        from explorer.assistant.utils import sample_rows_from_table, ROW_SAMPLE_SIZE
        SimpleQueryFactory(title="First Query")
        SimpleQueryFactory(title="Second Query")
        SimpleQueryFactory(title="Third Query")
        SimpleQueryFactory(title="Fourth Query")
        ret = sample_rows_from_table(CONN, "explorer_query")
        self.assertEqual(len(ret), ROW_SAMPLE_SIZE+1)  # includes header row

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
        ret = sample_rows_from_tables(CONN, ["explorer_query"])
        self.assertTrue("First Query" in ret)
        self.assertTrue("Second Query" in ret)

    def test_sample_rows_from_tables_no_tables(self):
        from explorer.assistant.utils import sample_rows_from_tables
        SimpleQueryFactory(title="First Query")
        SimpleQueryFactory(title="Second Query")
        ret = sample_rows_from_tables(CONN, [])
        self.assertEqual(ret, "")
