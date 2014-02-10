from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from explorer.tests.factories import SimpleQueryFactory
from explorer.models import Query
from explorer import app_settings


class TestQueryListView(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser('admin', 'admin@admin.com', 'pwd')
        self.client.login(username='admin', password='pwd')

    def test_admin_required(self):
        self.client.logout()
        resp = self.client.get(reverse("explorer_index"))
        self.assertTemplateUsed(resp, 'admin/login.html')


class TestQueryCreateView(TestCase):

    def setUp(self):
        self.admin = User.objects.create_superuser('admin', 'admin@admin.com', 'pwd')
        self.user = User.objects.create_user('user', 'user@user.com', 'pwd')

    def test_change_permission_required(self):
        self.client.login(username='user', password='pwd')
        resp = self.client.get(reverse("query_create"))
        self.assertTemplateUsed(resp, 'admin/login.html')

    def test_renders_with_title(self):
        self.client.login(username='admin', password='pwd')
        resp = self.client.get(reverse("query_create"))
        self.assertTemplateUsed(resp, 'explorer/query.html')
        self.assertContains(resp, "New Query")


class TestQueryDetailView(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser('admin', 'admin@admin.com', 'pwd')
        self.client.login(username='admin', password='pwd')

    def test_query_with_bad_sql_renders_error(self):
        query = SimpleQueryFactory(sql="error")
        resp = self.client.get(reverse("query_detail", kwargs={'query_id': query.id}))
        self.assertTemplateUsed(resp, 'explorer/query.html')
        self.assertContains(resp, "syntax error")

    def test_query_with_bad_sql_renders_error_on_save(self):
        query = SimpleQueryFactory(sql="select 1;")
        resp = self.client.post(reverse("query_detail", kwargs={'query_id': query.id}), data={'sql': 'error'})
        self.assertTemplateUsed(resp, 'explorer/query.html')
        self.assertContains(resp, "syntax error")

    def test_posting_query_saves_correctly(self):
        expected = 'select 2;'
        query = SimpleQueryFactory(sql="select 1;")
        data = model_to_dict(query)
        data['sql'] = expected
        self.client.post(reverse("query_detail", kwargs={'query_id': query.id}), data)
        self.assertEqual(Query.objects.get(pk=query.id).sql, expected)

    def test_change_permission_required_to_save_query(self):
        def not_allowed(user):
            return False

        old = app_settings.EXPLORER_PERMISSION_CHANGE
        app_settings.EXPLORER_PERMISSION_CHANGE = not_allowed
        User.add_to_class('sql_explorer_change', app_settings.EXPLORER_PERMISSION_CHANGE)

        query = SimpleQueryFactory()
        expected = query.sql
        resp = self.client.get(reverse("query_detail", kwargs={'query_id': query.id}))
        self.assertTemplateUsed(resp, 'explorer/query.html')

        self.client.post(reverse("query_detail", kwargs={'query_id': query.id}), {'sql': 'select 1;'})
        self.assertEqual(Query.objects.get(pk=query.id).sql, expected)

        app_settings.EXPLORER_PERMISSION_CHANGE = old
        User.add_to_class('sql_explorer_change', app_settings.EXPLORER_PERMISSION_CHANGE)

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

    def test_download_query(self):
        resp = self.client.get(reverse("query_download", kwargs={'query_id': self.query.id}))
        self.assertEqual(resp['content-type'], 'text/csv')

    def test_admin_required(self):
        self.client.logout()
        resp = self.client.get(reverse("query_download", kwargs={'query_id': self.query.id}))
        self.assertTemplateUsed(resp, 'admin/login.html')


class TestQueryPlayground(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser('admin', 'admin@admin.com', 'pwd')
        self.client.login(username='admin', password='pwd')

    def test_empty_playground_renders(self):
        resp = self.client.get(reverse("explorer_playground"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'explorer/play.html')

    def test_playground_renders_with_query_sql(self):
        query = SimpleQueryFactory(sql="select 1;")
        resp = self.client.get('%s?query_id=%s' % (reverse("explorer_playground"), query.id))
        self.assertTemplateUsed(resp, 'explorer/play.html')
        self.assertContains(resp, 'select 1;')

    def test_playground_renders_with_posted_sql(self):
        resp = self.client.post(reverse("explorer_playground"), {'sql': 'select 1;'})
        self.assertTemplateUsed(resp, 'explorer/play.html')
        self.assertContains(resp, 'select 1;')

    def test_query_with_no_resultset_doesnt_throw_error(self):
        query = SimpleQueryFactory(sql="")
        resp = self.client.get('%s?query_id=%s' % (reverse("explorer_playground"), query.id))
        self.assertTemplateUsed(resp, 'explorer/play.html')

    def test_admin_required(self):
        self.client.logout()
        resp = self.client.get(reverse("explorer_playground"))
        self.assertTemplateUsed(resp, 'admin/login.html')


class TestCSVFromSQL(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser('admin', 'admin@admin.com', 'pwd')
        self.client.login(username='admin', password='pwd')

    def test_admin_required(self):
        self.client.logout()
        resp = self.client.post(reverse("generate_csv"), {})
        self.assertTemplateUsed(resp, 'admin/login.html')

    def test_downloading_from_playground(self):
        sql = "select 1;"
        resp = self.client.post(reverse("generate_csv"), {'sql': sql})
        self.assertEqual(resp['content-type'], 'text/csv')


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


class TestParamsInViews(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser('admin', 'admin@admin.com', 'pwd')
        self.client.login(username='admin', password='pwd')
        self.query = SimpleQueryFactory(sql="select $$swap$$;")

    def test_retrieving_query_works_with_params(self):
        resp = self.client.get(reverse("query_detail", kwargs={'query_id': self.query.id}) + '?params={"swap":123}')
        self.assertContains(resp, "123")

    def test_query_in_playground_works_with_params(self):
        resp = self.client.get('%s?query_id=%s&params=%s' % (reverse("explorer_playground"), self.query.id, '{"swap":123}'))
        self.assertContains(resp, "123")

    def test_saving_non_executing_query_with__wrong_url_params_works(self):
        q = SimpleQueryFactory(sql="select $$swap$$;")
        data = model_to_dict(q)
        url = '%s?params=%s' % (reverse("query_detail", kwargs={'query_id': q.id}), '{"foo":123}')
        resp = self.client.post(url, data)
        self.assertContains(resp, 'saved')
