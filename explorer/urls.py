from django.conf.urls import url
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
    url(r'(?P<query_id>\d+)/$', QueryView.as_view(), name='query_detail'),
    url(r'(?P<query_id>\d+)/download$', download_query, name='query_download'),
    url(r'(?P<query_id>\d+)/csv$', view_csv_query, name='query_csv'),
    url(r'(?P<query_id>\d+)/email_csv$', email_csv_query, name='email_csv_query'),
    url(r'(?P<pk>\d+)/delete$', DeleteQueryView.as_view(), name='query_delete'),
    url(r'new/$', CreateQueryView.as_view(), name='query_create'),
    url(r'play/$', PlayQueryView.as_view(), name='explorer_playground'),
    url(r'csv$', download_csv_from_sql, name='generate_csv'),
    url(r'schema/$', schema, name='explorer_schema'),
    url(r'changelogs/$', ListQueryChangeLogView.as_view(), name='explorer_change_logs'),
    url(r'logs/$', ListQueryLogView.as_view(), name='explorer_logs'),
    url(r'format/$', format_sql, name='format_sql'),
    url(r'^$', ListQueryView.as_view(), name='explorer_index'),
]
