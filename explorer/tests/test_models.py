from django.test import TestCase
from explorer.tests.factories import SimpleQueryFactory
from explorer.tests.utils import AssertMethodIsCalled
from explorer.models import MSG_FAILED_BLACKLIST, QueryLog, Query


class TestQueryModel(TestCase):

    def test_blacklist_check_runs_before_execution(self):
        q = SimpleQueryFactory(sql='select 1;')
        with AssertMethodIsCalled(q, "passes_blacklist"):
            headers, data, duration, error = q.headers_and_data()

    def test_blacklist_prevents_bad_sql_from_executing(self):
        q = SimpleQueryFactory(sql='select 1 "delete";')
        headers, data, duration, error = q.headers_and_data()
        self.assertEqual(error, MSG_FAILED_BLACKLIST)

    def test_blacklist_prevents_bad_sql_with_params_from_executing(self):
        q = SimpleQueryFactory(sql="select '$$foo$$';")
        headers, data, duration, error = q.headers_and_data(params={"foo": "'; delete from *; select'"})
        self.assertEqual(error, MSG_FAILED_BLACKLIST)

    def test_params_get_merged(self):
        q = SimpleQueryFactory(sql="select '$$foo$$';")
        params = {'foo': 'bar', 'mux': 'qux'}
        self.assertEqual(q.available_params(params), {'foo': 'bar'})

    def test_query_log(self):
        self.assertEqual(0, QueryLog.objects.count())
        q = SimpleQueryFactory()
        q.log(None)
        self.assertEqual(1, QueryLog.objects.count())
        log = QueryLog.objects.first()
        self.assertEqual(log.run_by_user, None)
        self.assertEqual(log.query, q)
        self.assertFalse(log.is_playground)

    def test_playground_query_log(self):
        query = Query(sql='select 1;', title="Playground")
        query.log(None)
        log = QueryLog.objects.first()
        self.assertTrue(log.is_playground)