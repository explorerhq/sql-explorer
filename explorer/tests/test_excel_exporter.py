# -*- coding: utf-8 -*-
import unittest
from datetime import datetime

from django.db import connections
from django.test import TestCase
from django.utils import timezone

from explorer.app_settings import EXPLORER_DEFAULT_CONNECTION as CONN
from explorer.exporters import ExcelExporter
from explorer.models import QueryResult
from explorer.tests.factories import SimpleQueryFactory

try:
    import xlsxwriter
except ImportError:
    raise unittest.SkipTest("xlswriter not installed, skipping Excel tests")


class TestExcel(TestCase):

    def test_writing_excel(self):
        """
        This is a pretty crap test. It at least exercises the code.
        If anyone wants to go through the brain damage of actually building
        an 'expected' xlsx output and comparing it
        (https://github.com/jmcnamara/XlsxWriter/blob/master/xlsxwriter/
        test/helperfunctions.py)
        by all means submit a pull request!
        """
        res = QueryResult(
            SimpleQueryFactory(
                sql='select 1 as "a", 2 as ""',
                title='\\/*[]:?this title is longer than 32 characters'
            ).sql,
            connections[CONN]
        )

        res.execute_query()
        res.process()

        d = datetime.now()
        d = timezone.make_aware(d, timezone.get_current_timezone())

        res._data = [[1, None], ["Jenét", d]]

        res = ExcelExporter(
            query=SimpleQueryFactory()
        )._get_output(res).getvalue()

        expected = b'PK'

        self.assertEqual(res[:2], expected)

    def test_writing_dict_fields(self):
        res = QueryResult(
            SimpleQueryFactory(
                sql='select 1 as "a", 2 as ""',
                title='\\/*[]:?this title is longer than 32 characters'
            ).sql,
            connections[CONN]
        )

        res.execute_query()
        res.process()

        res._data = [[1, ['foo', 'bar']], [2, {'foo': 'bar'}]]

        res = ExcelExporter(
            query=SimpleQueryFactory()
        )._get_output(res).getvalue()

        expected = b'PK'

        self.assertEqual(res[:2], expected)
