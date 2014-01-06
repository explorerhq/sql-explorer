from django.test import TestCase
from explorer.tests.factories import SimpleQueryFactory
from explorer.utils import AssertMethodIsCalled
from explorer.models import MSG_FAILED_BLACKLIST


class TestQueryModel(TestCase):

    def test_blacklist_check_runs_before_execution(self):
        q = SimpleQueryFactory(sql='select 1;')
        with AssertMethodIsCalled(q, "passes_blacklist"):
            headers, data, error = q.headers_and_data()

    def test_blacklist_prevents_bad_sql_from_executing(self):
        q = SimpleQueryFactory(sql='select 1 "delete";')
        headers, data, error = q.headers_and_data()
        self.assertEqual(error, MSG_FAILED_BLACKLIST)

    def test_params_get_merged(self):
        q = SimpleQueryFactory(sql="select '$$foo$$';")
        q.params = {'foo': 'bar', 'mux': 'qux'}
        self.assertEqual(q.available_params(), {'foo': 'bar'})