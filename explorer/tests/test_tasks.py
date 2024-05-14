import unittest
from datetime import datetime, timedelta
from io import StringIO
from unittest.mock import patch, MagicMock
import os
import tempfile

from django.core import mail
from django.test import TestCase

from explorer import app_settings
from explorer.app_settings import EXPLORER_DEFAULT_CONNECTION as CONN
from explorer.models import QueryLog
from explorer.tasks import build_schema_cache_async, execute_query, snapshot_queries, truncate_querylogs, \
    remove_unused_sqlite_dbs
from explorer.tests.factories import SimpleQueryFactory


class TestTasks(TestCase):

    @unittest.skipIf(not app_settings.ENABLE_TASKS, "tasks not enabled")
    @patch("explorer.tasks.s3_upload")
    def test_async_results(self, mocked_upload):
        mocked_upload.return_value = "http://s3.com/your-file.csv"

        q = SimpleQueryFactory(
            sql='select 1 "a", 2 "b", 3 "c";', title="testquery"
        )
        execute_query(q.id, "cc@epantry.com")

        output = StringIO()
        output.write("a,b,c\r\n1,2,3\r\n")

        self.assertEqual(len(mail.outbox), 2)
        self.assertIn(
            "[SQL Explorer] Your query is running", mail.outbox[0].subject
        )
        self.assertIn("[SQL Explorer] Report ", mail.outbox[1].subject)
        self.assertEqual(
            mocked_upload
            .call_args[0][1].getvalue()
            .decode("utf-8-sig"),
            output.getvalue()
        )
        self.assertEqual(mocked_upload.call_count, 1)

    @unittest.skipIf(not app_settings.ENABLE_TASKS, "tasks not enabled")
    @patch("explorer.tasks.s3_upload")
    def test_async_results_fails_with_message(self, mocked_upload):
        mocked_upload.return_value = "http://s3.com/your-file.csv"

        q = SimpleQueryFactory(sql="select x from foo;", title="testquery")
        execute_query(q.id, "cc@epantry.com")

        output = StringIO()
        output.write("a,b,c\r\n1,2,3\r\n")

        self.assertEqual(len(mail.outbox), 2)
        self.assertIn("[SQL Explorer] Error ", mail.outbox[1].subject)
        self.assertEqual(mocked_upload.call_count, 0)

    @unittest.skipIf(not app_settings.ENABLE_TASKS, "tasks not enabled")
    @patch("explorer.tasks.s3_upload")
    def test_snapshots(self, mocked_upload):
        mocked_upload.return_value = "http://s3.com/your-file.csv"

        SimpleQueryFactory(snapshot=True)
        SimpleQueryFactory(snapshot=True)
        SimpleQueryFactory(snapshot=True)
        SimpleQueryFactory(snapshot=False)

        snapshot_queries()
        self.assertEqual(mocked_upload.call_count, 3)

    @unittest.skipIf(not app_settings.ENABLE_TASKS, "tasks not enabled")
    def test_truncating_querylogs(self):
        QueryLog(sql="foo").save()
        QueryLog.objects.filter(sql="foo").update(
            run_at=datetime.now() - timedelta(days=30)
        )
        QueryLog(sql="bar").save()
        QueryLog.objects.filter(sql="bar").update(
            run_at=datetime.now() - timedelta(days=29)
        )
        truncate_querylogs(30)
        self.assertEqual(QueryLog.objects.count(), 1)

    @unittest.skipIf(not app_settings.ENABLE_TASKS, "tasks not enabled")
    @patch("explorer.schema.build_schema_info")
    def test_build_schema_cache_async(self, mocked_build):
        mocked_build.return_value = [("table", [("column", "Integer")]),]
        schema = build_schema_cache_async(CONN)
        assert mocked_build.called
        self.assertEqual(schema, [("table", [("column", "Integer")]),])


class RemoveUnusedSQLiteDBsTestCase(TestCase):

    @patch("explorer.tasks.QueryLog")
    @patch("explorer.tasks.DatabaseConnection")
    def test_remove_unused_sqlite_dbs(self, MockDatabaseConnection, MockQueryLog):
        # Mock the settings
        days_inactivity = 30
        with patch("explorer.tasks.app_settings.EXPLORER_PRUNE_LOCAL_UPLOAD_COPY_DAYS_INACTIVITY", days_inactivity):
            with tempfile.TemporaryDirectory() as temp_dir:

                # Create a temporary SQLite file
                temp_db_path = os.path.join(temp_dir, "test_db1.sqlite")

                with open(temp_db_path, "w") as temp_db:
                    temp_db.write("")

                # Mock DatabaseConnection objects
                db1 = MagicMock()
                db1.local_name = temp_db_path
                db1.alias = "test_alias1"
                db1.host = "some_host"

                MockDatabaseConnection.objects.filter.return_value = [db1]

                recent_time = datetime.now() - timedelta(days=days_inactivity + 1)
                query_log1 = MagicMock()
                query_log1.run_at = recent_time

                mock_queryset = MagicMock()
                mock_queryset.first.return_value = query_log1

                def filter_side_effect(*args, **kwargs):
                    if kwargs.get("connection") == "test_alias1":
                        return mock_queryset
                    return MagicMock(first=MagicMock(return_value=None))

                MockQueryLog.objects.filter.side_effect = filter_side_effect

                # Call the function
                remove_unused_sqlite_dbs()

                # Assertions
                self.assertFalse(os.path.exists(temp_db_path))

    @patch("explorer.tasks.QueryLog")
    @patch("explorer.tasks.DatabaseConnection")
    def test_do_not_remove_recently_used_db(self, MockDatabaseConnection, MockQueryLog):
        days_inactivity = 30
        with patch("explorer.tasks.app_settings.EXPLORER_PRUNE_LOCAL_UPLOAD_COPY_DAYS_INACTIVITY", days_inactivity):
            with tempfile.TemporaryDirectory() as temp_dir:

                temp_db_path = os.path.join(temp_dir, "test_db1.sqlite")

                with open(temp_db_path, "w") as temp_db:
                    temp_db.write("")

                # Mock DatabaseConnection objects
                db1 = MagicMock()
                db1.local_name = temp_db_path
                db1.alias = "test_alias1"
                db1.host = "some_host"

                MockDatabaseConnection.objects.filter.return_value = [db1]

                recent_time = datetime.now() - timedelta(days=days_inactivity - 1)
                query_log1 = MagicMock()
                query_log1.run_at = recent_time

                mock_queryset = MagicMock()
                mock_queryset.first.return_value = query_log1

                def filter_side_effect(*args, **kwargs):
                    if kwargs.get("connection") == "test_alias1":
                        return mock_queryset
                    return MagicMock(first=MagicMock(return_value=None))

                MockQueryLog.objects.filter.side_effect = filter_side_effect

                # Call the function
                remove_unused_sqlite_dbs()

                # Assertions
                self.assertTrue(os.path.exists(temp_db_path))

    @patch("explorer.tasks.DatabaseConnection")
    def test_handle_missing_file_gracefully(self, MockDatabaseConnection):

        days_inactivity = 30
        with patch("explorer.tasks.app_settings.EXPLORER_PRUNE_LOCAL_UPLOAD_COPY_DAYS_INACTIVITY", days_inactivity):

            db1 = MagicMock()
            db1.local_name = "non_existent_db.sqlite"
            db1.alias = "test_alias1"
            db1.host = "some_host"
            MockDatabaseConnection.objects.filter.return_value = [db1]

            remove_unused_sqlite_dbs()

            # Since the file does not exist, we just ensure no exception is raised
            self.assertFalse(os.path.exists("non_existent_db.sqlite"))
