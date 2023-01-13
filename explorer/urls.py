from django.urls import path, re_path

from explorer.views import (
    CreateQueryView, DeleteQueryView, DownloadFromSqlView, DownloadQueryView, EmailCsvQueryView, ListQueryLogView,
    ListQueryView, PlayQueryView, QueryFavoritesView, QueryFavoriteView, QueryView, SchemaView, StreamQueryView,
    format_sql,
)


urlpatterns = [
    path(
        '<int:query_id>/', QueryView.as_view(), name='query_detail'
    ),
    path(
        '<int:query_id>/download', DownloadQueryView.as_view(),
        name='download_query'
    ),
    path(
        '<int:query_id>/stream', StreamQueryView.as_view(),
        name='stream_query'
    ),
    path('download', DownloadFromSqlView.as_view(), name='download_sql'),
    path(
        '<int:query_id>/email_csv', EmailCsvQueryView.as_view(),
        name='email_csv_query'
    ),
    path(
        '<int:pk>/delete', DeleteQueryView.as_view(), name='query_delete'
    ),
    path('new/', CreateQueryView.as_view(), name='query_create'),
    path('play/', PlayQueryView.as_view(), name='explorer_playground'),
    re_path(
        r'schema/(?P<connection>.+)$', SchemaView.as_view(),
        name='explorer_schema'
    ),
    path('logs/', ListQueryLogView.as_view(), name='explorer_logs'),
    path('format/', format_sql, name='format_sql'),
    path('favorites/', QueryFavoritesView.as_view(), name='query_favorites'),
    path('favorite/<int:query_id>', QueryFavoriteView.as_view(), name='query_favorite'),
    path('', ListQueryView.as_view(), name='explorer_index'),
]
