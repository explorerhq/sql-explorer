#encoding=utf8

from django.test import TestCase
from explorer.exporters import CSVExporter
from mock import Mock

class TestCsv(TestCase):

    def test_writing_unicode(self):
        res = Mock()
        res.headers = ['a', None]
        res.data = [[1, None], [u"Jenét", '1']]

        res = CSVExporter()._get_output(res)
        self.assertEqual(res, 'a,\r\n1,\r\nJenét,1\r\n')