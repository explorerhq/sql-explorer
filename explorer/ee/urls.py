from django.urls import path

from explorer.ee.db_connections.views import (
    UploadDbView,
    DatabaseConnectionsListView,
    DatabaseConnectionCreateView,
    DatabaseConnectionDetailView,
    DatabaseConnectionUpdateView,
    DatabaseConnectionDeleteView,
    DatabaseConnectionValidateView,
    DatabaseConnectionUploadCreateView,
    DatabaseConnectionRefreshView
)

ee_urls = [
    path("connections/", DatabaseConnectionsListView.as_view(), name="explorer_connections"),
    path("connections/upload/", UploadDbView.as_view(), name="explorer_upload"),
    path("connections/<int:pk>/", DatabaseConnectionDetailView.as_view(), name="explorer_connection_detail"),
    path("connections/new/", DatabaseConnectionCreateView.as_view(), name="explorer_connection_create"),
    path("connections/create_upload/", DatabaseConnectionUploadCreateView.as_view(), name="explorer_upload_create"),
    path("connections/<int:pk>/edit/", DatabaseConnectionUpdateView.as_view(), name="explorer_connection_update"),
    path("connections/<int:pk>/delete/", DatabaseConnectionDeleteView.as_view(), name="explorer_connection_delete"),
    path("connections/validate/", DatabaseConnectionValidateView.as_view(), name="explorer_connection_validate"),
    path("connections/<int:pk>/refresh/", DatabaseConnectionRefreshView.as_view(),
         name="explorer_connection_refresh")
]
