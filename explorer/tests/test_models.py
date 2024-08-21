import unittest
import os
from unittest.mock import Mock, patch, MagicMock

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from explorer import app_settings
from explorer.models import ColumnHeader, ColumnSummary, Query, QueryLog, QueryResult, DatabaseConnection
from explorer.tests.factories import SimpleQueryFactory
from explorer.ee.db_connections.utils import default_db_connection


class TestQueryModel(TestCase):

    def test_params_get_merged(self):
        q = SimpleQueryFactory(sql="select '$$foo$$';")
        q.params = {"foo": "bar", "mux": "qux"}
        self.assertEqual(q.available_params(), {"foo": "bar"})

    def test_default_params_used(self):
        q = SimpleQueryFactory(sql="select '$$foo:bar$$';")
        self.assertEqual(q.available_params(), {"foo": "bar"})

    def test_default_params_used_even_with_labels(self):
        q = SimpleQueryFactory(sql="select '$$foo|label:bar$$';")
        self.assertEqual(q.available_params(), {"foo": "bar"})

    def test_default_params_and_labels(self):
        q = SimpleQueryFactory(sql="select '$$foo|Label:bar$$';")
        self.assertEqual(q.available_params_w_labels(), {"foo": {"label": "Label", "val": "bar"}})

    def test_query_log(self):
        self.assertEqual(0, QueryLog.objects.count())
        q = SimpleQueryFactory()
        q.log(None)
        self.assertEqual(1, QueryLog.objects.count())
        log = QueryLog.objects.first()
        self.assertEqual(log.run_by_user, None)
        self.assertEqual(log.query, q)
        self.assertFalse(log.is_playground)
        self.assertEqual(log.database_connection, q.database_connection)

    def test_query_logs_final_sql(self):
        q = SimpleQueryFactory(sql="select '$$foo$$';")
        q.params = {"foo": "bar"}
        q.log(None)
        self.assertEqual(1, QueryLog.objects.count())
        log = QueryLog.objects.first()
        self.assertEqual(log.sql, "select 'bar';")

    def test_playground_query_log(self):
        query = Query(sql="select 1;", title="Playground")
        query.log(None)
        log = QueryLog.objects.first()
        self.assertTrue(log.is_playground)

    def test_shared(self):
        q = SimpleQueryFactory()
        q2 = SimpleQueryFactory()
        with self.settings(EXPLORER_USER_QUERY_VIEWS={"foo": [q.id]}):
            self.assertTrue(q.shared)
            self.assertFalse(q2.shared)

    def test_get_run_count(self):
        q = SimpleQueryFactory()
        self.assertEqual(q.get_run_count(), 0)
        expected = 4
        for _ in range(0, expected):
            q.log()
        self.assertEqual(q.get_run_count(), expected)

    def test_avg_duration(self):
        q = SimpleQueryFactory()
        self.assertIsNone(q.avg_duration())
        expected = 2.5
        ql = q.log()
        ql.duration = 2
        ql.save()
        ql = q.log()
        ql.duration = 3
        ql.save()
        self.assertEqual(q.avg_duration(), expected)

    def test_log_saves_duration(self):
        q = SimpleQueryFactory()
        res, ql = q.execute_with_logging(None)
        log = QueryLog.objects.first()
        self.assertEqual(log.duration, res.duration)
        self.assertTrue(log.success)
        self.assertIsNone(log.error)

    def test_log_saves_errors(self):
        q = SimpleQueryFactory()
        q.sql = "select wildly invalid query"
        q.save()
        try:
            q.execute_with_logging(None)
        except Exception:
            pass
        log = QueryLog.objects.first()
        self.assertFalse(log.success)
        self.assertIsNotNone(log.error)

    @unittest.skipIf(not app_settings.ENABLE_TASKS, "tasks not enabled")
    @patch("explorer.models.s3_url")
    @patch("explorer.models.get_s3_bucket")
    def test_get_snapshots_sorts_snaps(self, mocked_get_s3_bucket, mocked_s3_url):
        bucket = Mock()
        bucket.objects.filter = Mock()
        k1 = Mock()
        k1.key = "foo"
        k1.last_modified = "b"
        k2 = Mock()
        k2.key = "bar"
        k2.last_modified = "a"
        bucket.objects.filter.return_value = [k1, k2]
        mocked_get_s3_bucket.return_value = bucket
        mocked_s3_url.return_value = "http://s3.com/presigned_url"
        q = SimpleQueryFactory()
        snaps = q.snapshots
        self.assertEqual(bucket.objects.filter.call_count, 1)
        self.assertEqual(snaps[0].url, "http://s3.com/presigned_url")
        bucket.objects.filter.assert_called_once_with(Prefix=f"query-{q.id}/snap-")

    def test_final_sql_uses_merged_params(self):
        q = SimpleQueryFactory(sql="select '$$foo:bar$$', '$$qux$$';")
        q.params = {"qux": "mux"}
        expected = "select 'bar', 'mux';"
        self.assertEqual(q.final_sql(), expected)

    def test_final_sql_fails_blacklist_with_bad_param(self):
        q = SimpleQueryFactory(sql="$$command$$ from bar;")
        q.params = {"command": "delete"}
        expected = "delete from bar;"
        self.assertEqual(q.final_sql(), expected)
        with self.assertRaises(ValidationError):
            q.execute_query_only()

    def test_query_will_execute_with_null_database_connection(self):
        q = SimpleQueryFactory(sql="select 1;")
        q.database_connection_id = None
        q.save()
        q.refresh_from_db()
        qr = q.execute_query_only()
        self.assertEqual(qr.data[0], [1])


class TestQueryResults(TestCase):

    def setUp(self):
        conn = default_db_connection().as_django_connection()
        self.qr = QueryResult('select 1 as "foo", "qux" as "mux";', conn)

    def test_column_access(self):
        self.qr._data = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        self.assertEqual(self.qr.column(1), [2, 5, 8])

    def test_headers(self):
        self.assertEqual(str(self.qr.headers[0]), "foo")
        self.assertEqual(str(self.qr.headers[1]), "mux")

    def test_data(self):
        self.assertEqual(self.qr.data, [[1, "qux"]])

    def test_unicode_with_nulls(self):
        self.qr._headers = [ColumnHeader("num"), ColumnHeader("char")]
        self.qr._description = [("num",), ("char",)]
        self.qr._data = [[2, "a"], [3, None]]
        self.qr.process()
        self.assertEqual(self.qr.data, [[2, "a"], [3, None]])

    def test_summary_gets_built(self):
        self.qr.process()
        self.assertEqual(len([h for h in self.qr.headers if h.summary]), 1)
        self.assertEqual(str(self.qr.headers[0].summary), "foo")
        self.assertEqual(self.qr.headers[0].summary.stats["Sum"], 1.0)

    def test_summary_gets_built_for_multiple_cols(self):
        self.qr._headers = [ColumnHeader("a"), ColumnHeader("b")]
        self.qr._description = [("a",), ("b",)]
        self.qr._data = [[1, 10], [2, 20]]
        self.qr.process()
        self.assertEqual(len([h for h in self.qr.headers if h.summary]), 2)
        self.assertEqual(self.qr.headers[0].summary.stats["Sum"], 3.0)
        self.assertEqual(self.qr.headers[1].summary.stats["Sum"], 30.0)

    def test_numeric_detection(self):
        self.assertEqual(self.qr._get_numerics(), [0])

    def test_transforms_are_identified(self):
        self.qr._headers = [ColumnHeader("foo")]
        got = self.qr._get_transforms()
        self.assertEqual([(0, '<a href="{0}">{0}</a>')], got)

    def test_transform_alters_row(self):
        self.qr._headers = [ColumnHeader("foo"), ColumnHeader("qux")]
        self.qr._data = [[1, 2]]
        self.qr.process()
        self.assertEqual(['<a href="1">1</a>', 2], self.qr._data[0])

    def test_multiple_transforms(self):
        self.qr._headers = [ColumnHeader("foo"), ColumnHeader("bar")]
        self.qr._data = [[1, 2]]
        self.qr.process()
        self.assertEqual(['<a href="1">1</a>', "x: 2"], self.qr._data[0])

    def test_get_headers_no_results(self):
        self.qr._description = None
        self.assertEqual([ColumnHeader("--")][0].title, self.qr._get_headers()[0].title)


class TestColumnSummary(TestCase):

    def test_executes(self):
        res = ColumnSummary("foo", [1, 2, 3])
        self.assertEqual(res.stats, {"Min": 1, "Max": 3, "Avg": 2, "Sum": 6, "NUL": 0})

    def test_handles_null_as_zero(self):
        res = ColumnSummary("foo", [1, None, 5])
        self.assertEqual(res.stats, {"Min": 0, "Max": 5, "Avg": 2, "Sum": 6,  "NUL": 1})

    def test_empty_data(self):
        res = ColumnSummary("foo", [])
        self.assertEqual(res.stats, {"Min": 0, "Max": 0, "Avg": 0, "Sum": 0,  "NUL": 0})


class TestDatabaseConnection(TestCase):

    def test_cant_create_a_connection_with_conflicting_name(self):
        thrown = False
        try:
            conn = DatabaseConnection(alias="default")
            conn.save()
        except IntegrityError:
            thrown = True
        self.assertTrue(thrown)

    @patch("os.makedirs")
    @patch("os.path.exists", return_value=False)
    @patch("os.getcwd", return_value="/mocked/path")
    def test_local_name_calls_user_dbs_local_dir(self, mock_getcwd, mock_exists, mock_makedirs):
        connection = DatabaseConnection(
            alias="test",
            engine=DatabaseConnection.SQLITE,
            name="test_db.sqlite3",
            host="some-s3-bucket",
        )

        local_name = connection.local_name
        expected_path = "/mocked/path/user_dbs/test_db.sqlite3"

        # Check if the local_name property returns the correct path
        self.assertEqual(local_name, expected_path)

        # Ensure os.makedirs was called once since the directory does not exist
        mock_makedirs.assert_called_once_with("/mocked/path/user_dbs")

    @patch("explorer.utils.get_s3_bucket")
    def test_fingerprint_is_updated_after_download_and_download_is_not_called_again(self, mock_get_s3_bucket):
        # Setup
        mock_s3 = mock_get_s3_bucket.return_value

        connection = DatabaseConnection.objects.create(
            alias="test",
            engine=DatabaseConnection.SQLITE,
            name="test_db.sqlite3",
            host="some-s3-bucket",
        )

        # Define a function to mock S3 download
        def mock_download_file(path, filename):
            with open(filename, "w") as f:
                f.write("Initial content")

        mock_s3.download_file = MagicMock(side_effect=mock_download_file)

        # First download
        connection.download_sqlite_if_needed()

        # Check that the file was "downloaded" (in this case, created)
        self.assertTrue(os.path.exists(connection.local_name))

        # Check that the fingerprint was updated
        self.assertIsNotNone(connection.upload_fingerprint)
        initial_fingerprint = connection.upload_fingerprint

        # Mock S3 download to track calls
        mock_s3.download_file.reset_mock()

        # Second attempt to download
        connection.download_sqlite_if_needed()

        # Check that download was not called again
        mock_s3.download_file.assert_not_called()

        # Check that the fingerprint hasn't changed
        connection.refresh_from_db()
        self.assertEqual(connection.upload_fingerprint, initial_fingerprint)

        # Modify the file to simulate changes
        with open(connection.local_name, "w") as f:
            f.write("Modified content")

        # Third attempt to download
        connection.download_sqlite_if_needed()

        # Check that download was called again
        mock_s3.download_file.assert_called_once()

        # Check that the fingerprint has been updated back to the original
        connection.refresh_from_db()
        self.assertEqual(connection.upload_fingerprint, initial_fingerprint)

    def test_default_is_set(self):
        orig_default = default_db_connection()
        new_default = DatabaseConnection(alias="new1", engine=DatabaseConnection.SQLITE, name="test_db.sqlite3",
                                         default=True)
        new_default.save()
        orig_default.refresh_from_db()
        self.assertFalse(orig_default.default)
        self.assertEqual(new_default.id, default_db_connection().id)
        self.assertEqual(DatabaseConnection.objects.filter(default=True).count(), 1)
