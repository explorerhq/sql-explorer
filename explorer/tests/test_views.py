import importlib
import json
import time
import unittest
from unittest.mock import Mock, patch, MagicMock

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.conf import settings
from django.db import connections
from django.forms.models import model_to_dict
from django.shortcuts import redirect
from django.test import TestCase
from django.urls import reverse

from explorer import app_settings
from explorer.app_settings import EXPLORER_DEFAULT_CONNECTION as CONN
from explorer.app_settings import EXPLORER_TOKEN
from explorer.models import MSG_FAILED_BLACKLIST, Query, QueryFavorite, QueryLog, DatabaseConnection
from explorer.tests.factories import QueryLogFactory, SimpleQueryFactory
from explorer.utils import user_can_see_query
from explorer.ee.db_connections.views import DatabaseConnectionsListView


def reload_app_settings():
    """
    Reload app settings, otherwise changes from testing context manager won't take effect
    app_settings are loaded at time of import
    """
    importlib.reload(app_settings)


class TestQueryListView(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser(
            "admin", "admin@admin.com", "pwd"
        )
        self.client.login(username="admin", password="pwd")

    def test_admin_required(self):
        self.client.logout()
        resp = self.client.get(reverse("explorer_index"))
        self.assertTemplateUsed(resp, "admin/login.html")

    def test_headers(self):
        SimpleQueryFactory(title="foo - bar1")
        SimpleQueryFactory(title="foo - bar2")
        SimpleQueryFactory(title="foo - bar3")
        SimpleQueryFactory(title="qux - mux")
        resp = self.client.get(reverse("explorer_index"))
        self.assertContains(resp, "foo (3)")
        self.assertContains(resp, "foo - bar2")
        self.assertContains(resp, "qux - mux")

    def test_permissions_show_only_allowed_queries(self):
        self.client.logout()
        q1 = SimpleQueryFactory(title="canseethisone")
        q2 = SimpleQueryFactory(title="nope")
        user = User.objects.create_user("user", "user@user.com", "pwd")
        self.client.login(username="user", password="pwd")
        with self.settings(EXPLORER_USER_QUERY_VIEWS={user.id: [q1.id]}):
            resp = self.client.get(reverse("explorer_index"))
        self.assertTemplateUsed(resp, "explorer/query_list.html")
        self.assertContains(resp, q1.title)
        self.assertNotContains(resp, q2.title)

    def test_run_count(self):
        q = SimpleQueryFactory(title="foo - bar1")
        for _ in range(0, 4):
            q.log()
        resp = self.client.get(reverse("explorer_index"))
        self.assertContains(resp, "4</td>")


class TestQueryCreateView(TestCase):

    def setUp(self):
        self.admin = User.objects.create_superuser(
            "admin", "admin@admin.com", "pwd"
        )
        self.user = User.objects.create_user(
            "user", "user@user.com", "pwd"
        )

    def test_change_permission_required(self):
        self.client.login(username="user", password="pwd")
        resp = self.client.get(reverse("query_create"))
        self.assertTemplateUsed(resp, "admin/login.html")

    def test_renders_with_title(self):
        self.client.login(username="admin", password="pwd")
        resp = self.client.get(reverse("query_create"))
        self.assertTemplateUsed(resp, "explorer/query.html")
        self.assertContains(resp, "New Query")


def custom_view(request):
    return redirect("/custom/login")


class TestQueryDetailView(TestCase):
    databases = ["default", "alt"]

    def setUp(self):
        self.user = User.objects.create_superuser(
            "admin", "admin@admin.com", "pwd"
        )
        self.client.login(username="admin", password="pwd")

    def test_query_with_bad_sql_renders_error(self):
        query = SimpleQueryFactory(sql="error")
        resp = self.client.get(
            reverse("query_detail", kwargs={"query_id": query.id})
        )
        self.assertTemplateUsed(resp, "explorer/query.html")
        self.assertContains(resp, "syntax error")

    def test_query_with_bad_sql_renders_error_on_save(self):
        query = SimpleQueryFactory(sql="select 1;")
        resp = self.client.post(
            reverse("query_detail", kwargs={"query_id": query.id}),
            data={"sql": "error"}
        )
        self.assertTemplateUsed(resp, "explorer/query.html")
        self.assertContains(resp, "syntax error")

    def test_posting_query_saves_correctly(self):
        expected = "select 2;"
        query = SimpleQueryFactory(sql="select 1;")
        data = model_to_dict(query)
        data["sql"] = expected
        self.client.post(
            reverse("query_detail", kwargs={"query_id": query.id}),
            data
        )
        self.assertEqual(Query.objects.get(pk=query.id).sql, expected)

    def test_change_permission_required_to_save_query(self):
        query = SimpleQueryFactory()
        expected = query.sql
        resp = self.client.get(
            reverse("query_detail", kwargs={"query_id": query.id})
        )
        self.assertTemplateUsed(resp, "explorer/query.html")

        self.client.post(
            reverse("query_detail", kwargs={"query_id": query.id}),
            {"sql": "select 1;"}
        )
        self.assertEqual(Query.objects.get(pk=query.id).sql, expected)

    def test_modified_date_gets_updated_after_viewing_query(self):
        query = SimpleQueryFactory()
        old = query.last_run_date
        time.sleep(0.1)
        self.client.get(
            reverse("query_detail", kwargs={"query_id": query.id})
        )
        self.assertNotEqual(old, Query.objects.get(pk=query.id).last_run_date)

    def test_doesnt_render_results_if_show_is_none(self):
        query = SimpleQueryFactory(sql="select 6870+1;")
        resp = self.client.get(
            reverse(
                "query_detail", kwargs={"query_id": query.id}
            ) + "?show=0"
        )
        self.assertTemplateUsed(resp, "explorer/query.html")
        self.assertNotContains(resp, "6871")

    def test_doesnt_render_results_if_show_is_none_on_post(self):
        query = SimpleQueryFactory(sql="select 6870+1;")
        resp = self.client.post(
            reverse(
                "query_detail", kwargs={"query_id": query.id}
            ) + "?show=0",
            {"sql": "select 6870+2;"}
        )
        self.assertTemplateUsed(resp, "explorer/query.html")
        self.assertNotContains(resp, "6872")

    def test_doesnt_render_results_if_params_and_no_autorun(self):
        with self.settings(EXPLORER_AUTORUN_QUERY_WITH_PARAMS=False):
            reload_app_settings()
            query = SimpleQueryFactory(sql="select 6870+3 where 1=$$myparam:1$$;")
            resp = self.client.get(
                reverse(
                    "query_detail", kwargs={"query_id": query.id}
                )
            )
            self.assertTemplateUsed(resp, "explorer/query.html")
            self.assertNotContains(resp, "6873")

    def test_does_render_results_if_params_and_autorun(self):
        with self.settings(EXPLORER_AUTORUN_QUERY_WITH_PARAMS=True):
            reload_app_settings()
            query = SimpleQueryFactory(sql="select 6870+4 where 1=$$myparam:1$$;")
            resp = self.client.get(
                reverse(
                    "query_detail", kwargs={"query_id": query.id}
                )
            )
            self.assertTemplateUsed(resp, "explorer/query.html")
            self.assertContains(resp, "6874")

    def test_does_render_label_if_params_and_autorun(self):
        with self.settings(EXPLORER_AUTORUN_QUERY_WITH_PARAMS=True):
            reload_app_settings()
            query = SimpleQueryFactory(sql="select 6870+4 where 1=$$myparam|test my param label:1$$;")
            resp = self.client.get(
                reverse(
                    "query_detail", kwargs={"query_id": query.id}
                )
            )
            self.assertTemplateUsed(resp, "explorer/query.html")
            self.assertContains(resp, "test my param label")

    def test_admin_required(self):
        self.client.logout()
        query = SimpleQueryFactory()
        resp = self.client.get(
            reverse("query_detail", kwargs={"query_id": query.id})
        )
        self.assertTemplateUsed(resp, "admin/login.html")

    def test_admin_required_with_explorer_no_permission_setting(self):
        self.client.logout()
        query = SimpleQueryFactory()
        with self.settings(EXPLORER_NO_PERMISSION_VIEW="explorer.tests.test_views.custom_view"):
            resp = self.client.get(
                reverse("query_detail", kwargs={"query_id": query.id})
            )
            self.assertRedirects(
                resp, "/custom/login",
                target_status_code=404
            )

    def test_individual_view_permission(self):
        self.client.logout()
        user = User.objects.create_user("user1", "user@user.com", "pwd")
        self.client.login(username="user1", password="pwd")

        query = SimpleQueryFactory(sql="select 123+1")

        with self.settings(EXPLORER_USER_QUERY_VIEWS={user.id: [query.id]}):
            resp = self.client.get(
                reverse("query_detail", kwargs={"query_id": query.id})
            )
        self.assertTemplateUsed(resp, "explorer/query.html")
        self.assertContains(resp, "124")

    def test_header_token_auth(self):
        self.client.logout()

        query = SimpleQueryFactory(sql="select 123+1")

        with self.settings(EXPLORER_TOKEN_AUTH_ENABLED=True):
            resp = self.client.get(
                reverse("query_detail", kwargs={"query_id": query.id}),
                **{"HTTP_X_API_TOKEN": EXPLORER_TOKEN}
            )
        self.assertTemplateUsed(resp, "explorer/query.html")
        self.assertContains(resp, "124")

    def test_url_token_auth(self):
        self.client.logout()

        query = SimpleQueryFactory(sql="select 123+1")

        with self.settings(EXPLORER_TOKEN_AUTH_ENABLED=True):
            resp = self.client.get(
                reverse(
                    "query_detail", kwargs={"query_id": query.id}
                ) + f"?token={EXPLORER_TOKEN}"
            )
        self.assertTemplateUsed(resp, "explorer/query.html")
        self.assertContains(resp, "124")

    def test_user_query_views(self):
        request = Mock()

        request.user.is_anonymous = True
        kwargs = {}
        self.assertFalse(user_can_see_query(request, **kwargs))

        request.user.is_anonymous = True
        self.assertFalse(user_can_see_query(request, **kwargs))

        kwargs = {"query_id": 123}
        request.user.is_anonymous = False
        self.assertFalse(user_can_see_query(request, **kwargs))

        request.user.id = 99
        with self.settings(EXPLORER_USER_QUERY_VIEWS={99: [111, 123]}):
            self.assertTrue(user_can_see_query(request, **kwargs))

    @unittest.skipIf(not app_settings.ENABLE_TASKS, "tasks not enabled")
    @patch("explorer.models.get_s3_bucket")
    def test_query_snapshot_renders(self, mocked_conn):
        conn = Mock()
        conn.objects.filter = Mock()
        k1 = Mock()
        k1.generate_url.return_value = "http://s3.com/foo"
        k1.last_modified = "2015-01-01"
        k2 = Mock()
        k2.generate_url.return_value = "http://s3.com/bar"
        k2.last_modified = "2015-01-02"
        conn.objects.filter.return_value = [k1, k2]
        mocked_conn.return_value = conn

        query = SimpleQueryFactory(sql="select 1;", snapshot=True)
        resp = self.client.get(
            reverse("query_detail", kwargs={"query_id": query.id})
        )
        self.assertContains(resp, "2015-01-01")
        self.assertContains(resp, "2015-01-02")

    def test_failing_blacklist_means_query_doesnt_execute(self):
        conn = connections[CONN]
        start = len(conn.queries)
        query = SimpleQueryFactory(sql="select 1;")
        resp = self.client.post(
            reverse("query_detail", kwargs={"query_id": query.id}),
            data={"sql": "delete from auth_user;"}
        )
        end = len(conn.queries)

        self.assertTemplateUsed(resp, "explorer/query.html")
        self.assertContains(resp, MSG_FAILED_BLACKLIST % "")

        self.assertEqual(start, end)

    def test_fullscreen(self):
        query = SimpleQueryFactory(sql="select 1;")
        resp = self.client.get(
            reverse(
                "query_detail", kwargs={"query_id": query.id}
            ) + "?fullscreen=1"
        )
        self.assertTemplateUsed(resp, "explorer/fullscreen.html")

    def test_multiple_connections_integration(self):
        from explorer.app_settings import EXPLORER_CONNECTIONS
        from explorer.connections import connections

        c1_alias = EXPLORER_CONNECTIONS["SQLite"]
        conn = connections()[c1_alias]
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS animals (name text NOT NULL);")
        c.execute("INSERT INTO animals ( name ) VALUES ('peacock')")

        c2_alias = EXPLORER_CONNECTIONS["Another"]
        conn = connections()[c2_alias]
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS animals (name text NOT NULL);")
        c.execute("INSERT INTO animals ( name ) VALUES ('superchicken')")

        query = SimpleQueryFactory(
            sql="select name from animals;", connection=c1_alias
        )
        resp = self.client.get(
            reverse("query_detail", kwargs={"query_id": query.id})
        )
        self.assertContains(resp, "peacock")

        query = SimpleQueryFactory(
            sql="select name from animals;", connection=c2_alias
        )
        resp = self.client.get(
            reverse("query_detail", kwargs={"query_id": query.id})
        )
        self.assertContains(resp, "superchicken")


class TestDownloadView(TestCase):
    def setUp(self):
        self.query = SimpleQueryFactory(sql="select 1;")
        self.user = User.objects.create_superuser(
            "admin", "admin@admin.com", "pwd"
        )
        self.client.login(username="admin", password="pwd")

    def test_admin_required(self):
        self.client.logout()
        resp = self.client.get(
            reverse("download_query", kwargs={"query_id": self.query.id})
        )
        self.assertTemplateUsed(resp, "admin/login.html")

    def test_params_in_download(self):
        q = SimpleQueryFactory(sql="select '$$foo$$';")
        url = "{}?params={}".format(
            reverse("download_query", kwargs={"query_id": q.id}),
            "foo:123"
        )
        resp = self.client.get(url)
        self.assertContains(resp, "'123'")

    def test_download_defaults_to_csv(self):
        query = SimpleQueryFactory()
        url = reverse("download_query", args=[query.pk])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["content-type"], "text/csv")

    def test_download_csv(self):
        query = SimpleQueryFactory()
        url = reverse("download_query", args=[query.pk]) + "?format=csv"

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["content-type"], "text/csv")

    def test_bad_query_gives_500(self):
        query = SimpleQueryFactory(sql="bad")
        url = reverse("download_query", args=[query.pk]) + "?format=csv"

        response = self.client.get(url)

        self.assertEqual(response.status_code, 500)

    def test_download_json(self):
        query = SimpleQueryFactory()
        url = reverse("download_query", args=[query.pk]) + "?format=json"

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["content-type"], "application/json")

        json_data = json.loads(response.content.decode("utf-8"))
        self.assertIsInstance(json_data, list)
        self.assertEqual(len(json_data), 1)
        self.assertEqual(json_data, [{"TWO": 2}])


class TestQueryPlayground(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser(
            "admin", "admin@admin.com", "pwd"
        )
        self.client.login(username="admin", password="pwd")

    def test_empty_playground_renders(self):
        resp = self.client.get(reverse("explorer_playground"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "explorer/play.html")

    def test_playground_renders_with_query_sql(self):
        query = SimpleQueryFactory(sql="select 1;")
        resp = self.client.get(
            "{}?query_id={}".format(reverse("explorer_playground"), query.id)
        )
        self.assertTemplateUsed(resp, "explorer/play.html")
        self.assertContains(resp, "select 1;")

    def test_playground_renders_with_posted_sql(self):
        resp = self.client.post(
            reverse("explorer_playground"),
            {"sql": "select 1+3400;"}
        )
        self.assertTemplateUsed(resp, "explorer/play.html")
        self.assertContains(resp, "3401")

    def test_playground_doesnt_render_with_posted_sql_if_show_is_none(self):
        resp = self.client.post(
            reverse("explorer_playground") + "?show=0",
            {"sql": "select 1+3400;"}
        )
        self.assertTemplateUsed(resp, "explorer/play.html")
        self.assertNotContains(resp, "3401")

    def test_playground_renders_with_empty_posted_sql(self):
        resp = self.client.post(reverse("explorer_playground"), {"sql": ""})
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "explorer/play.html")

    def test_query_with_no_resultset_doesnt_throw_error(self):
        query = SimpleQueryFactory(sql="")
        resp = self.client.get(
            "{}?query_id={}".format(reverse("explorer_playground"), query.id)
        )
        self.assertTemplateUsed(resp, "explorer/play.html")

    def test_admin_required(self):
        self.client.logout()
        resp = self.client.get(reverse("explorer_playground"))
        self.assertTemplateUsed(resp, "admin/login.html")

    def test_admin_required_with_no_permission_view_setting(self):
        self.client.logout()
        with self.settings(EXPLORER_NO_PERMISSION_VIEW="explorer.tests.test_views.custom_view"):
            resp = self.client.get(reverse("explorer_playground"))
            self.assertRedirects(
                resp,
                "/custom/login",
                target_status_code=404
            )

    def test_loads_query_from_log(self):
        querylog = QueryLogFactory()
        resp = self.client.get(
            "{}?querylog_id={}".format(
                reverse("explorer_playground"), querylog.id
            )
        )
        self.assertContains(resp, "FOUR")

    def test_fails_blacklist(self):
        resp = self.client.post(
            reverse("explorer_playground"),
            {"sql": "delete from auth_user;"}
        )
        self.assertTemplateUsed(resp, "explorer/play.html")
        self.assertContains(resp, MSG_FAILED_BLACKLIST % "")

    def test_fullscreen(self):
        query = SimpleQueryFactory(sql="")
        resp = self.client.get(
            "{}?query_id={}&fullscreen=1".format(
                reverse("explorer_playground"),
                query.id
            )
        )
        self.assertTemplateUsed(resp, "explorer/fullscreen.html")


class TestCSVFromSQL(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser(
            "admin", "admin@admin.com", "pwd"
        )
        self.client.login(username="admin", password="pwd")

    def test_admin_required(self):
        self.client.logout()
        resp = self.client.post(reverse("download_sql"), {})
        self.assertTemplateUsed(resp, "admin/login.html")

    def test_downloading_from_playground(self):
        sql = "select 1;"
        resp = self.client.post(reverse("download_sql"), {"sql": sql})
        self.assertIn("attachment", resp["Content-Disposition"])
        self.assertEqual("text/csv", resp["content-type"])
        ql = QueryLog.objects.first()
        self.assertIn(
            f'filename="Playground-{ql.id}.csv"',
            resp["Content-Disposition"]
        )

    def test_stream_csv_from_query(self):
        q = SimpleQueryFactory()
        resp = self.client.get(
            reverse("stream_query", kwargs={"query_id": q.id})
        )
        self.assertEqual("text/csv", resp["content-type"])


class TestSQLDownloadViews(TestCase):
    databases = ["default", "alt"]

    def setUp(self):
        self.user = User.objects.create_superuser(
            "admin", "admin@admin.com", "pwd"
        )
        self.client.login(username="admin", password="pwd")

    def test_sql_download_csv(self):
        url = reverse("download_sql") + "?format=csv"

        response = self.client.post(url, {"sql": "select 1;"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["content-type"], "text/csv")

    def test_sql_download_respects_connection(self):
        from explorer.app_settings import EXPLORER_CONNECTIONS
        from explorer.connections import connections

        c1_alias = EXPLORER_CONNECTIONS["SQLite"]
        conn = connections()[c1_alias]
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS animals (name text NOT NULL);")
        c.execute("INSERT INTO animals ( name ) VALUES ('peacock')")

        c2_alias = EXPLORER_CONNECTIONS["Another"]
        conn = connections()[c2_alias]
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS animals (name text NOT NULL);")
        c.execute("INSERT INTO animals ( name ) VALUES ('superchicken')")

        url = reverse("download_sql") + "?format=csv"

        response = self.client.post(
            url,
            {"sql": "select * from animals;", "connection": c2_alias}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "superchicken")

    def test_sql_download_csv_with_custom_delim(self):
        url = reverse("download_sql") + "?format=csv&delim=|"

        response = self.client.post(url, {"sql": "select 1,2;"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["content-type"], "text/csv")
        self.assertEqual(response.content.decode("utf-8-sig"), "1|2\r\n1|2\r\n")

    def test_sql_download_csv_with_tab_delim(self):
        url = reverse("download_sql") + "?format=csv&delim=tab"

        response = self.client.post(url, {"sql": "select 1,2;"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["content-type"], "text/csv")
        self.assertEqual(response.content.decode("utf-8-sig"), "1\t2\r\n1\t2\r\n")

    def test_sql_download_csv_with_bad_delim(self):
        url = reverse("download_sql") + "?format=csv&delim=foo"

        response = self.client.post(url, {"sql": "select 1,2;"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["content-type"], "text/csv")
        self.assertEqual(response.content.decode("utf-8-sig"), "1,2\r\n1,2\r\n")

    def test_sql_download_json(self):
        url = reverse("download_sql") + "?format=json"

        response = self.client.post(url, {"sql": "select 1;"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["content-type"], "application/json")


class TestSchemaView(TestCase):

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_superuser(
            "admin", "admin@admin.com", "pwd"
        )
        self.client.login(username="admin", password="pwd")

    def test_returns_schema_contents(self):
        resp = self.client.get(
            reverse("explorer_schema", kwargs={"connection": CONN})
        )
        self.assertContains(resp, "explorer_query")
        self.assertTemplateUsed(resp, "explorer/schema.html")

    def test_returns_404_if_conn_doesnt_exist(self):
        resp = self.client.get(
            reverse("explorer_schema", kwargs={"connection": "foo"})
        )
        self.assertEqual(resp.status_code, 404)

    def test_admin_required(self):
        self.client.logout()
        resp = self.client.get(
            reverse("explorer_schema", kwargs={"connection": CONN})
        )
        self.assertTemplateUsed(resp, "admin/login.html")

    @unittest.skipIf(not app_settings.ENABLE_TASKS, "tasks not enabled")
    @patch("explorer.schema.do_async")
    def test_builds_async(self, mocked_async_check):
        mocked_async_check.return_value = True
        resp = self.client.get(
            reverse("explorer_schema", kwargs={"connection": CONN})
        )
        self.assertTemplateUsed(resp, "explorer/schema_building.html")
        resp = self.client.get(
            reverse("explorer_schema", kwargs={"connection": CONN})
        )
        self.assertTemplateUsed(resp, "explorer/schema.html")


class TestFormat(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser(
            "admin", "admin@admin.com", "pwd"
        )
        self.client.login(username="admin", password="pwd")

    def test_returns_formatted_sql(self):
        resp = self.client.post(
            reverse("format_sql"),
            data={"sql": "select * from explorer_query"}
        )
        resp = json.loads(resp.content.decode("utf-8"))
        self.assertIn("\n", resp["formatted"])
        self.assertIn("explorer_query", resp["formatted"])


class TestParamsInViews(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser(
            "admin", "admin@admin.com", "pwd"
        )
        self.client.login(username="admin", password="pwd")
        self.query = SimpleQueryFactory(sql="select $$swap$$;")

    def test_retrieving_query_works_with_params(self):
        resp = self.client.get(
            reverse(
                "query_detail", kwargs={"query_id": self.query.id}
            ) + "?params=swap:123}"
        )
        self.assertContains(resp, "123")

    def test_saving_non_executing_query_with__wrong_url_params_works(self):
        q = SimpleQueryFactory(sql="select $$swap$$;")
        data = model_to_dict(q)
        url = "{}?params={}".format(
            reverse("query_detail", kwargs={"query_id": q.id}),
            "foo:123"
        )
        resp = self.client.post(url, data)
        self.assertContains(resp, "saved")

    def test_users_without_change_permissions_can_use_params(self):
        resp = self.client.get(
            reverse(
                "query_detail", kwargs={"query_id": self.query.id}
            ) + "?params=swap:123}"
        )
        self.assertContains(resp, "123")


class TestCreatedBy(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser(
            "admin", "admin@admin.com", "pwd"
        )
        self.user2 = User.objects.create_superuser(
            "admin2", "admin2@admin.com", "pwd"
        )
        self.client.login(username="admin", password="pwd")
        self.query = SimpleQueryFactory.build(created_by_user=self.user)
        self.data = model_to_dict(self.query)
        del self.data["id"]
        self.data["created_by_user_id"] = self.user2.id

    def test_query_update_doesnt_change_created_user(self):
        self.query.save()
        self.client.post(
            reverse("query_detail", kwargs={"query_id": self.query.id}),
            self.data
        )
        q = Query.objects.get(id=self.query.id)
        self.assertEqual(q.created_by_user_id, self.user.id)

    def test_new_query_gets_created_by_logged_in_user(self):
        self.client.post(reverse("query_create"), self.data)
        q = Query.objects.first()
        self.assertEqual(q.created_by_user_id, self.user.id)


class TestQueryLog(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser(
            "admin", "admin@admin.com", "pwd"
        )
        self.client.login(username="admin", password="pwd")

    def test_playground_saves_query_to_log(self):
        self.client.post(reverse("explorer_playground"), {"sql": "select 1;"})
        log = QueryLog.objects.first()
        self.assertTrue(log.is_playground)
        self.assertEqual(log.sql, "select 1;")

    # Since it will be saved on the initial query creation, no need to log it
    def test_creating_query_does_not_save_to_log(self):
        query = SimpleQueryFactory()
        self.client.post(reverse("query_create"), model_to_dict(query))
        self.assertEqual(0, QueryLog.objects.count())

    def test_query_saves_to_log(self):
        query = SimpleQueryFactory()
        data = model_to_dict(query)
        data["sql"] = "select 12345;"
        self.client.post(
            reverse("query_detail", kwargs={"query_id": query.id}),
            data
        )
        self.assertEqual(1, QueryLog.objects.count())

    def test_query_gets_logged_and_appears_on_log_page(self):
        query = SimpleQueryFactory()
        data = model_to_dict(query)
        data["sql"] = "select 12345;"
        self.client.post(
            reverse("query_detail", kwargs={"query_id": query.id}),
            data
        )
        resp = self.client.get(reverse("explorer_logs"))
        self.assertContains(resp, "select 12345;")

    def test_admin_required(self):
        self.client.logout()
        resp = self.client.get(reverse("explorer_logs"))
        self.assertTemplateUsed(resp, "admin/login.html")

    def test_is_playground(self):
        self.assertTrue(QueryLog(sql="foo").is_playground)

        q = SimpleQueryFactory()
        self.assertFalse(QueryLog(sql="foo", query_id=q.id).is_playground)


class TestEmailQuery(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser(
            "admin", "admin@admin.com", "pwd"
        )
        self.client.login(username="admin", password="pwd")

    @patch("explorer.views.email.execute_query")
    def test_email_calls_task(self, mocked_execute):
        query = SimpleQueryFactory()
        url = reverse("email_csv_query", kwargs={"query_id": query.id})
        self.client.post(
            url,
            data={"email": "foo@bar.com"},
            **{"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}
        )
        self.assertEqual(mocked_execute.delay.call_count, 1)

    def test_email_403(self):
        query = SimpleQueryFactory()
        url = reverse("email_csv_query", kwargs={"query_id": query.id})
        response = self.client.post(
            url,
            data={},
            **{"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}
        )
        self.assertEqual(response.status_code, 403)

    def test_email_no_xml_403(self):
        query = SimpleQueryFactory()
        url = reverse("email_csv_query", kwargs={"query_id": query.id})
        response = self.client.post(
            url,
            data={},
        )
        self.assertEqual(response.status_code, 403)


class TestQueryFavorites(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser(
            "admin", "admin@admin.com", "pwd"
        )
        self.client.login(username="admin", password="pwd")
        self.q = SimpleQueryFactory(title="query for x, y")
        QueryFavorite.objects.create(user=self.user, query=self.q)

    def test_returns_favorite_list(self):
        resp = self.client.get(
            reverse("query_favorites")
        )
        self.assertContains(resp, "query for x, y")


class TestQueryFavorite(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser(
            "admin", "admin@admin.com", "pwd"
        )
        self.client.login(username="admin", password="pwd")
        self.q = SimpleQueryFactory(title="query for x, y")

    def test_toggle(self):
        resp = self.client.post(
            reverse("query_favorite",  args=(self.q.id,))
        )
        resp = json.loads(resp.content.decode("utf-8"))
        self.assertTrue(resp["is_favorite"])
        resp = self.client.post(
            reverse("query_favorite",  args=(self.q.id,))
        )
        resp = json.loads(resp.content.decode("utf-8"))
        self.assertFalse(resp["is_favorite"])


class UploadDbViewTest(TestCase):

    def setUp(self):
        DatabaseConnection.objects.all().delete()
        self.user = User.objects.create_superuser(
            "admin", "admin@admin.com", "pwd"
        )
        self.client.login(username="admin", password="pwd")

    def test_post_csv_file(self):
        file_content = "col1,col2\nval1,val2\nval3,val4"
        uploaded_file = SimpleUploadedFile("test.csv", file_content.encode(), content_type="text/csv")

        with patch("explorer.ee.db_connections.views.is_csv", return_value=True), \
            patch("explorer.ee.db_connections.views.csv_to_typed_df") as mock_csv_to_typed_df, \
            patch("explorer.ee.db_connections.views.pandas_to_sqlite") as mock_pandas_to_sqlite, \
            patch("explorer.ee.db_connections.views.upload_sqlite") as mock_upload_sqlite:
            mock_csv_to_typed_df.return_value = MagicMock()
            mock_pandas_to_sqlite.return_value = b"sqlite_content"

            response = self.client.post(reverse("explorer_upload"), {"file": uploaded_file})

            self.assertEqual(response.status_code, 200)
            self.assertJSONEqual(response.content, {"success": True})
            print(DatabaseConnection.objects.first().alias)
            self.assertTrue(DatabaseConnection.objects.filter(alias=f"test_{self.user.id}.db").exists())
            mock_upload_sqlite.assert_called_once()
            mock_csv_to_typed_df.assert_called_once()

    def test_post_no_file(self):
        response = self.client.post(reverse("explorer_upload"))

        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {"error": "No file provided"})

    def test_delete_existing_connection(self):
        dbc = DatabaseConnection.objects.create(
            alias="test.db",
            engine=DatabaseConnection.SQLITE,
            name="test.db",
            host="s3_path/test.db"
        )

        with patch("explorer.ee.db_connections.views.delete_from_s3") as mock_delete_from_s3:
            response = self.client.delete(reverse("explorer_connection_delete", kwargs={"pk": dbc.id}))

            self.assertEqual(response.status_code, 302)
            self.assertFalse(DatabaseConnection.objects.filter(alias="test.db").exists())
            mock_delete_from_s3.assert_called_once_with("s3_path/test.db")

    def test_delete_non_existing_connection(self):
        response = self.client.delete("/upload/?alias=nonexistent.db")

        self.assertEqual(response.status_code, 404)

    @patch("explorer.ee.db_connections.views.EXPLORER_MAX_UPLOAD_SIZE", 1024*1024)
    def test_post_file_too_large(self):
        file_content = "a" * (1024 * 1024 + 1)  # Slightly larger 1 MB
        uploaded_file = SimpleUploadedFile("large_file.csv", file_content.encode(), content_type="text/csv")

        response = self.client.post(reverse("explorer_upload"), {"file": uploaded_file})

        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {"error": "File size exceeds the limit of 5 MB"})


class DatabaseConnectionsListViewTestCase(TestCase):

    def setUp(self):
        # Setting up the app settings for testing
        self.original_explorer_connections = settings.EXPLORER_CONNECTIONS
        settings.EXPLORER_CONNECTIONS = {
            "default": "default_connection_alias",
        }

    def tearDown(self):
        # Restore the original app settings
        settings.EXPLORER_CONNECTIONS = self.original_explorer_connections

    def test_queryset_combines_connections(self):
        # Create a DatabaseConnection instance
        db_conn = DatabaseConnection.objects.create(name="Test Connection", alias="test_alias")

        # Instantiate the view and call get_queryset
        view = DatabaseConnectionsListView()
        queryset = view.get_queryset()

        # Convert queryset to a list for easy comparison
        queryset_list = list(queryset)

        # Check if both the created connection and the connections from app settings are in the queryset
        self.assertIn(db_conn, queryset_list)
        self.assertTrue(any(conn.alias == "default" for conn in queryset_list))


class DatabaseConnectionValidateViewTestCase(TestCase):

    def setUp(self):

        self.user = User.objects.create_superuser(
            "admin", "admin@admin.com", "pwd"
        )
        self.client.login(username="admin", password="pwd")
        self.url = reverse("explorer_connection_validate")
        self.valid_data = {
            "alias": "test_alias",
            "engine": "django.db.backends.sqlite3",
            "name": ":memory:",
            "user": "",
            "password": "",
            "host": "",
            "port": "",
        }
        self.invalid_data = {
            "alias": "",
            "engine": "",
            "name": "",
            "user": "",
            "password": "",
            "host": "",
            "port": "",
        }

    def test_validate_connection_success(self):
        response = self.client.post(self.url, data=self.valid_data)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"success": True})

    def test_validate_connection_invalid_form(self):
        response = self.client.post(self.url, data=self.invalid_data)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"success": False, "error": "Invalid form data"})

    def test_update_existing_connection(self):
        DatabaseConnection.objects.create(alias="test_alias", engine="django.db.backends.sqlite3", name=":memory:")
        response = self.client.post(self.url, data=self.valid_data)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"success": True})

    @patch("explorer.ee.db_connections.views.create_django_style_connection")
    def test_database_connection_error(self, mock_create_connection):
        from django.db import OperationalError
        mock_create_connection.side_effect = OperationalError("Connection error")
        response = self.client.post(self.url, data=self.valid_data)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"success": False, "error": "Connection error"})


# The idea is to render all of these views, to ensure that errors haven't been introduced in the templates
class SimpleViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser(
            "admin", "admin@admin.com", "pwd"
        )
        self.client.login(username="admin", password="pwd")
        self.connection = DatabaseConnection.objects.create(
            alias="test_alias",
            engine="django.db.backends.sqlite3",
            name=":memory:",
            user="",
            password="",
            host="",
            port=""
        )

    def test_database_connection_detail_view(self):
        response = self.client.get(reverse("explorer_connection_detail", args=[self.connection.pk]))
        self.assertEqual(response.status_code, 200)

    def test_database_connection_create_view(self):
        response = self.client.get(reverse("explorer_connection_create"))
        self.assertEqual(response.status_code, 200)

    def test_database_connection_update_view(self):
        response = self.client.get(reverse("explorer_connection_update", args=[self.connection.pk]))
        self.assertEqual(response.status_code, 200)

    def test_database_connections_list_view(self):
        response = self.client.get(reverse("explorer_connections"))
        self.assertEqual(response.status_code, 200)

    def test_database_connection_delete_view(self):
        response = self.client.get(reverse("explorer_connection_delete", args=[self.connection.pk]))
        self.assertEqual(response.status_code, 200)

