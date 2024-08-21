import unittest
from datetime import datetime, timedelta
from io import StringIO
from unittest.mock import patch
import os

from django.core import mail
from django.test import TestCase
from django.utils import timezone

from explorer import app_settings
from explorer.models import QueryLog
from explorer.ee.db_connections.models import DatabaseConnection
from explorer.tasks import execute_query, snapshot_queries, truncate_querylogs, \
    remove_unused_sqlite_dbs
from explorer.tests.factories import SimpleQueryFactory


class TestTasks(TestCase):

    @unittest.skipIf(not app_settings.ENABLE_TASKS, "tasks not enabled")
    @patch("explorer.tasks.s3_csv_upload")
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
    @patch("explorer.tasks.s3_csv_upload")
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
    @patch("explorer.tasks.s3_csv_upload")
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
        delete_time = timezone.make_aware(datetime.now() - timedelta(days=31), timezone.get_default_timezone())
        QueryLog.objects.filter(sql="foo").update(
            run_at=delete_time
        )

        QueryLog(sql="bar").save()
        ok_time = timezone.make_aware(datetime.now() - timedelta(days=29), timezone.get_default_timezone())
        QueryLog.objects.filter(sql="bar").update(
            run_at=ok_time
        )
        truncate_querylogs(30)
        self.assertEqual(QueryLog.objects.count(), 1)


class RemoveUnusedSQLiteDBsTestCase(TestCase):

    def set_up_the_things(self, offset):
        dbc = DatabaseConnection(
            alias="localconn",
            name="localconn",
            engine=DatabaseConnection.SQLITE,
            host="foo"
        )
        dbc.save()
        days = app_settings.EXPLORER_PRUNE_LOCAL_UPLOAD_COPY_DAYS_INACTIVITY

        with open(dbc.local_name, "w") as temp_db:
            temp_db.write("")

        recent_time = timezone.make_aware(datetime.now() - timedelta(days=days + offset),
                                          timezone.get_default_timezone())
        ql = QueryLog(sql="foo", database_connection=dbc)
        ql.save()
        QueryLog.objects.filter(id=ql.id).update(run_at=recent_time)  # Have to sidestep the auto_add_now

        return dbc, ql

    def test_remove_unused_sqlite_dbs(self):
        dbc, ql = self.set_up_the_things(1)
        remove_unused_sqlite_dbs()
        self.assertFalse(os.path.exists(dbc.local_name))
        dbc.delete()
        ql.delete()

    def test_do_not_remove_recently_used_db(self):
        dbc, ql = self.set_up_the_things(-1)
        remove_unused_sqlite_dbs()
        self.assertTrue(os.path.exists(dbc.local_name))
        os.remove(dbc.local_name)
        dbc.delete()
        ql.delete()
