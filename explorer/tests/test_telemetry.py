from django.test import TestCase
from explorer.telemetry import instance_identifier, _gather_summary_stats, Stat, StatNames, _get_install_quarter
from unittest.mock import patch, MagicMock
from django.core.cache import cache
from datetime import datetime


class TestTelemetry(TestCase):

    def setUp(self):
        cache.delete("last_stat_sent_time")

    def test_instance_identifier(self):
        v = instance_identifier()
        self.assertEqual(len(v), 36)

        # Doesn't change after calling it again
        v = instance_identifier()
        self.assertEqual(len(v), 36)

    def test_gather_summary_stats(self):
        res = _gather_summary_stats()
        self.assertEqual(res["total_query_count"], 0)
        self.assertEqual(res["default_database"], "sqlite")

    @patch("explorer.telemetry.threading.Thread")
    @patch("explorer.app_settings")
    def test_stats_not_sent_too_frequently(self, mocked_app_settings, mocked_thread):
        mocked_app_settings.EXPLORER_ENABLE_ANONYMOUS_STATS = True
        mocked_app_settings.UNSAFE_RENDERING = True
        mocked_app_settings.EXPLORER_CHARTS_ENABLED = True
        mocked_app_settings.has_assistant = MagicMock(return_value=True)
        mocked_app_settings.db_connections_enabled = MagicMock(return_value=True)
        mocked_app_settings.ENABLE_TASKS = True
        s1 = Stat(StatNames.QUERY_RUN, {"foo": "bar"})
        s2 = Stat(StatNames.QUERY_RUN, {"mux": "qux"})
        s3 = Stat(StatNames.QUERY_RUN, {"bar": "baz"})

        # once for s1 and once for summary stats
        s1.track()
        self.assertEqual(mocked_thread.call_count, 2)

        # both the s2 track call is suppressed, and the summary stat call
        s2.track()
        self.assertEqual(mocked_thread.call_count, 2)

        # clear the cache, which should cause track() for the stat to work, but not send summary stats
        cache.clear()
        s3.track()
        self.assertEqual(mocked_thread.call_count, 3)

    @patch("explorer.telemetry.threading.Thread")
    @patch("explorer.app_settings")
    def test_stats_not_sent_if_disabled(self, mocked_app_settings, mocked_thread):
        mocked_app_settings.EXPLORER_ENABLE_ANONYMOUS_STATS = False
        s1 = Stat(StatNames.QUERY_RUN, {"foo": "bar"})
        s1.track()
        self.assertEqual(mocked_thread.call_count, 0)

    @patch("explorer.telemetry.MigrationRecorder.Migration.objects.filter")
    def test_get_install_quarter_with_no_migrations(self, mock_filter):
        mock_filter.return_value.order_by.return_value.first.return_value = None
        result = _get_install_quarter()
        self.assertIsNone(result)

    @patch("explorer.telemetry.MigrationRecorder.Migration.objects.filter")
    def test_get_install_quarter_edge_cases(self, mock_filter):
        # Test edge cases like end of year and start of year
        dates = [datetime(2022, 12, 31), datetime(2023, 1, 1), datetime(2023, 3, 31), datetime(2023, 4, 1)]
        results = ["Q4-2022", "Q1-2023", "Q1-2023", "Q2-2023"]

        for date, expected in zip(dates, results):
            with self.subTest(date=date):
                mock_migration = MagicMock()
                mock_migration.applied = date
                mock_filter.return_value.order_by.return_value.first.return_value = mock_migration

                result = _get_install_quarter()
                self.assertEqual(result, expected)
