from django.urls import re_path
from explorer.views import (
    QueryView,
    CreateQueryView,
    PlayQueryView,
    DeleteQueryView,
    ListQueryView,
    ListQueryLogView,
    ListQueryChangeLogView,
    download_query,
    view_csv_query,
    email_csv_query,
    download_csv_from_sql,
    schema,
    format_sql,
)

urlpatterns = [
        re_path(r'(?P<query_id>\d+)/$', QueryView.as_view(), name='query_detail'),
        re_path(r'(?P<query_id>\d+)/download$', download_query, name='query_download'),
        re_path(r'(?P<query_id>\d+)/csv$', view_csv_query, name='query_csv'),
        re_path(r'(?P<query_id>\d+)/email_csv$', email_csv_query, name='email_csv_query'),
        re_path(r'(?P<pk>\d+)/delete$', DeleteQueryView.as_view(), name='query_delete'),
        re_path(r'new/$', CreateQueryView.as_view(), name='query_create'),
        re_path(r'play/$', PlayQueryView.as_view(), name='explorer_playground'),
        re_path(r'csv$', download_csv_from_sql, name='generate_csv'),
        re_path(r'schema/$', schema, name='explorer_schema'),
        re_path(r'changelogs/$', ListQueryChangeLogView.as_view(), name='explorer_change_logs'),
        re_path(r'logs/$', ListQueryLogView.as_view(), name='explorer_logs'),
        re_path(r'format/$', format_sql, name='format_sql'),
        re_path(r'^$', ListQueryView.as_view(), name='explorer_index'),
    ]
