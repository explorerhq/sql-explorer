from django.conf.urls import patterns, url
from explorer.views import QueryView, CreateQueryView, PlayQueryView, DeleteQueryView, ListQueryView, ListQueryLogView

urlpatterns = patterns('',
    url(r'(?P<query_id>\d+)/$', QueryView.as_view(), name='query_detail'),
    url(r'(?P<query_id>\d+)/download$', 'explorer.views.download_query', name='query_download'),
    url(r'(?P<query_id>\d+)/csv$', 'explorer.views.view_csv_query', name='query_csv'),
    url(r'(?P<query_id>\d+)/email_csv$', 'explorer.views.email_csv_query', name='email_csv_query'),
    url(r'(?P<pk>\d+)/delete$', DeleteQueryView.as_view(), name='query_delete'),
    url(r'new/$', CreateQueryView.as_view(), name='query_create'),
    url(r'play/$', PlayQueryView.as_view(), name='explorer_playground'),
    url(r'csv$', 'explorer.views.download_csv_from_sql', name='generate_csv'),
    url(r'schema/$', 'explorer.views.schema', name='explorer_schema'),
    url(r'logs/$', ListQueryLogView.as_view(), name='explorer_logs'),
    url(r'format/$', 'explorer.views.format_sql', name='format_sql'),
    url(r'^$', ListQueryView.as_view(), name='explorer_index'),
)
