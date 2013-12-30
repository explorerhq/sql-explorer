from django.conf.urls import patterns, url
from explorer.views import QueryView, CreateQueryView, PlayQueryView, DeleteQueryView, ListQueryView

urlpatterns = patterns('',
    url(r'(?P<query_id>\d+)/$', QueryView.as_view(), name='query_detail'),
    url(r'(?P<query_id>\d+)/download$', 'explorer.views.download_query', name='query_download'),
    url(r'(?P<pk>\d+)/delete$', DeleteQueryView.as_view(), name='query_delete'),
    url(r'new/$', CreateQueryView.as_view(), name='query_create'),
    url(r'play/$', PlayQueryView.as_view(), name='explorer_playground'),
    url(r'csv$', 'explorer.views.csv_from_sql', name='generate_csv'),
    url(r'schema/$', 'explorer.views.schema', name='explorer_schema'),
    url(r'$', ListQueryView.as_view(), name='explorer_index'),
)