from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from explorer.tests.factories import SimpleQueryFactory
from explorer.models import Query


class TestQueryListView(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser('admin', 'admin@admin.com', 'pwd')
        self.client.login(username='admin', password='pwd')

    def test_admin_required(self):
        self.client.logout()
        resp = self.client.get(reverse("explorer_index"))
        self.assertTemplateUsed(resp, 'admin/login.html')


class TestQueryDetailView(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser('admin', 'admin@admin.com', 'pwd')
        self.client.login(username='admin', password='pwd')

    def test_query_with_bad_sql_renders_error(self):
        query = SimpleQueryFactory(sql="error")
        resp = self.client.get(reverse("query_detail", kwargs={'query_id': query.id}))
        self.assertTemplateUsed(resp, 'explorer/query.html')

    def test_posting_query_saves_correctly(self):
        expected = 'select 2;'
        query = SimpleQueryFactory(sql="select 1;")
        data = model_to_dict(query)
        data['sql'] = expected
        self.client.post(reverse("query_detail", kwargs={'query_id': query.id}), data)
        self.assertEqual(Query.objects.get(pk=query.id).sql, expected)

    def test_admin_required(self):
        self.client.logout()
        query = SimpleQueryFactory(sql="before")
        resp = self.client.get(reverse("query_detail", kwargs={'query_id': query.id}))
        self.assertTemplateUsed(resp, 'admin/login.html')


class TestDownloadView(TestCase):
    def setUp(self):
        self.query = SimpleQueryFactory(sql="select 1;")
        self.user = User.objects.create_superuser('admin', 'admin@admin.com', 'pwd')
        self.client.login(username='admin', password='pwd')

    def test_query_with_bad_sql_renders_error(self):
        resp = self.client.get(reverse("csv_download", kwargs={'query_id': self.query.id}))
        self.assertEqual(resp['content-type'], 'text/csv')

    def test_admin_required(self):
        self.client.logout()
        resp = self.client.get(reverse("csv_download", kwargs={'query_id': self.query.id}))
        self.assertTemplateUsed(resp, 'admin/login.html')


class TestQueryPlayground(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser('admin', 'admin@admin.com', 'pwd')
        self.client.login(username='admin', password='pwd')

    def test_empty_playground_renders(self):
        resp = self.client.get(reverse("explorer_playground"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'explorer/play.html')

    def test_playground_renders_with_prepopulated_sql(self):
        query = SimpleQueryFactory(sql="select 1;")
        resp = self.client.get('%s?query_id=%s' % (reverse("explorer_playground"), query.id))
        self.assertTemplateUsed(resp, 'explorer/play.html')
        self.assertContains(resp, 'select 1;')

    def test_admin_required(self):
        self.client.logout()
        resp = self.client.get(reverse("explorer_playground"))
        self.assertTemplateUsed(resp, 'admin/login.html')


class TestSchemaView(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser('admin', 'admin@admin.com', 'pwd')
        self.client.login(username='admin', password='pwd')

    def test_returns_schema_contents(self):
        resp = self.client.get(reverse("explorer_schema"))
        self.assertContains(resp, "explorer_query")
        self.assertTemplateUsed(resp, 'explorer/schema.html')

    def test_admin_required(self):
        self.client.logout()
        resp = self.client.get(reverse("explorer_schema"))
        self.assertTemplateUsed(resp, 'admin/login.html')