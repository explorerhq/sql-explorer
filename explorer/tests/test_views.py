from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from explorer.tests.factories import SimpleQueryFactory, QueryLogFactory
from explorer.models import Query, QueryLog
from explorer.views import user_can_see_query
from django.conf import settings
from mock import Mock
import time


class TestQueryListView(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser('admin', 'admin@admin.com', 'pwd')
        self.client.login(username='admin', password='pwd')

    def test_admin_required(self):
        self.client.logout()
        resp = self.client.get(reverse("explorer_index"))
        self.assertTemplateUsed(resp, 'admin/login.html')

    def test_headers(self):
        SimpleQueryFactory(title='foo - bar1')
        SimpleQueryFactory(title='foo - bar2')
        SimpleQueryFactory(title='foo - bar3')
        SimpleQueryFactory(title='qux - mux')
        resp = self.client.get(reverse("explorer_index"))
        self.assertContains(resp, 'foo (3)')
        self.assertContains(resp, 'foo - bar2')
        self.assertContains(resp, 'qux - mux')


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

        #old = app_settings.EXPLORER_PERMISSION_CHANGE
        #app_settings.EXPLORER_PERMISSION_CHANGE = lambda u: False

        query = SimpleQueryFactory()
        expected = query.sql
        resp = self.client.get(reverse("query_detail", kwargs={'query_id': query.id}))
        self.assertTemplateUsed(resp, 'explorer/query.html')

        self.client.post(reverse("query_detail", kwargs={'query_id': query.id}), {'sql': 'select 1;'})
        self.assertEqual(Query.objects.get(pk=query.id).sql, expected)

        #app_settings.EXPLORER_PERMISSION_CHANGE = old

    def test_modified_date_gets_updated_after_viewing_query(self):
        query = SimpleQueryFactory()
        old = query.last_run_date
        time.sleep(0.1)
        self.client.get(reverse("query_detail", kwargs={'query_id': query.id}))
        self.assertNotEqual(old, Query.objects.get(pk=query.id).last_run_date)

    def test_admin_required(self):
        self.client.logout()
        query = SimpleQueryFactory()
        resp = self.client.get(reverse("query_detail", kwargs={'query_id': query.id}))
        self.assertTemplateUsed(resp, 'admin/login.html')

    def test_individual_view_permission(self):
        self.client.logout()
        user = User.objects.create_user('user1', 'user@user.com', 'pwd')
        self.client.login(username='user1', password='pwd')

        query = SimpleQueryFactory(sql="select 123")

        with self.settings(EXPLORER_USER_QUERY_VIEWS={user.id: [query.id]}):
            resp = self.client.get(reverse("query_detail", kwargs={'query_id': query.id}))
        self.assertTemplateUsed(resp, 'explorer/query.html')
        self.assertContains(resp, "123")

    def test_user_query_views(self):
        request = Mock()

        request.user.is_anonymous = Mock(return_value=True)
        kwargs = {}
        self.assertFalse(user_can_see_query(request, kwargs))

        request.user.is_anonymous = Mock(return_value=True)
        self.assertFalse(user_can_see_query(request, kwargs))

        kwargs = {'query_id': 123}
        request.user.is_anonymous = Mock(return_value=False)
        self.assertFalse(user_can_see_query(request, kwargs))

        request.user.id = 99
        with self.settings(EXPLORER_USER_QUERY_VIEWS={99: [111, 123]}):
            self.assertTrue(user_can_see_query(request, kwargs))


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

    def test_params_in_download(self):
        q = SimpleQueryFactory(sql="select '$$foo$$';")
        url = '%s?params=%s' % (reverse("query_download", kwargs={'query_id': q.id}), '{"foo":123}')
        resp = self.client.get(url)
        self.assertContains(resp, "'123'")


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

    def test_loads_query_from_log(self):
        querylog = QueryLogFactory()
        resp = self.client.get('%s?querylog_id=%s' % (reverse("explorer_playground"), querylog.id))
        self.assertContains(resp, "FOUR")


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

    def test_saving_non_executing_query_with__wrong_url_params_works(self):
        q = SimpleQueryFactory(sql="select $$swap$$;")
        data = model_to_dict(q)
        url = '%s?params=%s' % (reverse("query_detail", kwargs={'query_id': q.id}), '{"foo":123}')
        resp = self.client.post(url, data)
        self.assertContains(resp, 'saved')

    def test_users_without_change_permissions_can_use_params(self):

        #old = app_settings.EXPLORER_PERMISSION_CHANGE
        #app_settings.EXPLORER_PERMISSION_CHANGE = lambda u: False

        resp = self.client.get(reverse("query_detail", kwargs={'query_id': self.query.id}) + '?params={"swap":123}')
        self.assertContains(resp, "123")

        #app_settings.EXPLORER_PERMISSION_CHANGE = old


class TestCreatedBy(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser('admin', 'admin@admin.com', 'pwd')
        self.user2 = User.objects.create_superuser('admin2', 'admin2@admin.com', 'pwd')
        self.client.login(username='admin', password='pwd')
        self.query = SimpleQueryFactory.build()
        self.data = model_to_dict(self.query)
        self.data["created_by_user"] = 2

    def test_query_update_doesnt_change_created_user(self):
        self.query.save()
        self.client.post(reverse("query_detail", kwargs={'query_id': self.query.id}), self.data)
        q = Query.objects.get(id=self.query.id)
        self.assertEqual(q.created_by_user_id, 1)

    def test_new_query_gets_created_by_logged_in_user(self):
        self.client.post(reverse("query_create"), self.data)
        q = Query.objects.first()
        self.assertEqual(q.created_by_user_id, 1)


class TestQueryLog(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser('admin', 'admin@admin.com', 'pwd')
        self.client.login(username='admin', password='pwd')

    def test_playground_saves_query_to_log(self):
        self.client.post(reverse("explorer_playground"), {'sql': 'select 1;'})
        log = QueryLog.objects.first()
        self.assertTrue(log.is_playground)
        self.assertEqual(log.sql, 'select 1;')

    # Since it will be saved on the initial query creation, no need to log it
    def test_creating_query_does_not_save_to_log(self):
        query = SimpleQueryFactory()
        self.client.post(reverse("query_create"), model_to_dict(query))
        self.assertEqual(0, QueryLog.objects.count())

    def test_changing_query_saves_to_log(self):
        query = SimpleQueryFactory()
        data = model_to_dict(query)
        data['sql'] = 'select 12345;'
        self.client.post(reverse("query_detail", kwargs={'query_id': query.id}), data)
        self.assertEqual(1, QueryLog.objects.count())

    def test_unchanged_query_doesnt_save_to_log(self):
        query = SimpleQueryFactory()
        self.client.post(reverse("query_detail", kwargs={'query_id': query.id}), model_to_dict(query))
        self.assertEqual(0, QueryLog.objects.count())

    def test_retrieving_query_doesnt_save_to_log(self):
        query = SimpleQueryFactory()
        self.client.get(reverse("query_detail", kwargs={'query_id': query.id}))
        self.assertEqual(0, QueryLog.objects.count())

    def test_query_gets_logged_and_appears_on_log_page(self):
        query = SimpleQueryFactory()
        data = model_to_dict(query)
        data['sql'] = 'select 12345;'
        self.client.post(reverse("query_detail", kwargs={'query_id': query.id}), data)
        resp = self.client.get(reverse("explorer_logs"))
        self.assertContains(resp, 'select 12345;')

    def test_admin_required(self):
        self.client.logout()
        resp = self.client.get(reverse("explorer_logs"))
        self.assertTemplateUsed(resp, 'admin/login.html')