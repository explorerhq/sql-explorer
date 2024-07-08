from django.urls import path

from explorer.ee.db_connections.views import (
    UploadDbView,
    DatabaseConnectionsListView,
    DatabaseConnectionCreateView,
    DatabaseConnectionDetailView,
    DatabaseConnectionUpdateView,
    DatabaseConnectionDeleteView,
    DatabaseConnectionValidateView
)

ee_urls = [
    path("connections/", DatabaseConnectionsListView.as_view(), name="explorer_connections"),
    path("connections/upload/", UploadDbView.as_view(), name="explorer_upload"),
    path("connections/<int:pk>/", DatabaseConnectionDetailView.as_view(), name="explorer_connection_detail"),
    path("connections/new/", DatabaseConnectionCreateView.as_view(), name="explorer_connection_create"),
    path("connections/<int:pk>/edit/", DatabaseConnectionUpdateView.as_view(), name="explorer_connection_update"),
    path("connections/<int:pk>/delete/", DatabaseConnectionDeleteView.as_view(), name="explorer_connection_delete"),
    # There are two URLs here because the form can call validate from /connections/new/ or from /connections/<pk>/edit/
    # which have different relative paths. It's easier to just provide both of these URLs rather than deal with this
    # client-side.
    path("connections/validate/", DatabaseConnectionValidateView.as_view(), name="explorer_connection_validate"),
    path("connections/<int:pk>/validate/", DatabaseConnectionValidateView.as_view(),
         name="explorer_connection_validate_with_pk"),
]
