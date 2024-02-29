from django.test import TestCase
from explorer.tracker import instance_identifier, gather_summary_stats


class TestTracker(TestCase):

    def test_instance_identifier(self):
        v = instance_identifier()

        # The SHA-256 hash produces a fixed-length output of 256 bits.
        # When represented as a hexadecimal string, each byte (8 bits) is
        # represented by 2 hex chars. 256/8*2 = 64
        self.assertEqual(len(v), 64)

    def test_gather_summary_stats(self):
        res = gather_summary_stats()
        self.assertEqual(res["total_query_count"], 0)
        self.assertEqual(res["default_database"], "sqlite")
