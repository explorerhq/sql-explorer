from django.test import TestCase
from django.core.urlresolvers import reverse
from report.tests.factories import SimpleReportFactory


class TestReportViews(TestCase):

    def test_report_with_bad_sql_renders_error(self):
        report = SimpleReportFactory(sql="error")
        resp = self.client.get(reverse("report_detail", kwargs={'report_id': report.id}))
        self.assertEqual(resp.status_code, 200)