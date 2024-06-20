import logging
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views import View
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.db.utils import OperationalError
from explorer.models import DatabaseConnection
from explorer.ee.db_connections.utils import (
    upload_sqlite,
    create_connection_for_uploaded_sqlite,
    is_csv,
    csv_to_typed_df,
    pandas_to_sqlite
)
from explorer import app_settings
from explorer.app_settings import EXPLORER_MAX_UPLOAD_SIZE
from explorer.ee.db_connections.forms import DatabaseConnectionForm
from explorer.utils import delete_from_s3
from explorer.views.auth import PermissionRequiredMixin
from explorer.views.mixins import ExplorerContextMixin
from explorer.ee.db_connections.utils import create_django_style_connection


logger = logging.getLogger(__name__)


class UploadDbView(PermissionRequiredMixin, View):

    permission_required = "connections_permission"

    def post(self, request):
        file = request.FILES.get("file")
        if file:
            if file.size > EXPLORER_MAX_UPLOAD_SIZE:
                return JsonResponse({"error": "File size exceeds the limit of 5 MB"}, status=400)

            f_name = file.name
            f_bytes = file.read()

            if is_csv(file):
                df = csv_to_typed_df(f_bytes)

                try:
                    f_bytes = pandas_to_sqlite(df)
                except Exception as e:  # noqa
                    logger.exception(f"Exception while parsing file {f_name}: {e}")
                    return JsonResponse({"error": "Error while parsing the file."}, status=400)

                f_name = f_name.replace("csv", "db")

            try:
                s3_path = f"user_dbs/user_{request.user.id}/{f_name}"
                upload_sqlite(f_bytes, s3_path)
            except Exception as e:  # noqa
                logger.exception(f"Exception while uploading file {f_name}: {e}")
                return JsonResponse({"error": "Error while uploading file."}, status=400)

            create_connection_for_uploaded_sqlite(f_name, request.user.id, s3_path)
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"error": "No file provided"}, status=400)


class DatabaseConnectionsListView(PermissionRequiredMixin, ExplorerContextMixin, ListView):

    context_object_name = "sqlite_uploads"
    permission_required = "connections_permission"
    template_name = "connections/connections.html"
    model = DatabaseConnection

    def get_queryset(self):
        qs = list(DatabaseConnection.objects.all())
        for _, alias in app_settings.EXPLORER_CONNECTIONS.items():
            django_conn = DatabaseConnection.from_django_connection(alias)
            if django_conn:
                qs.append(django_conn)
        return qs


class DatabaseConnectionDetailView(PermissionRequiredMixin, DetailView):
    permission_required = "connections_permission"
    model = DatabaseConnection
    template_name = "connections/database_connection_detail.html"


class DatabaseConnectionCreateView(PermissionRequiredMixin, ExplorerContextMixin, CreateView):
    permission_required = "connections_permission"
    model = DatabaseConnection
    form_class = DatabaseConnectionForm
    template_name = "connections/database_connection_form.html"
    success_url = reverse_lazy("explorer_connections")


class DatabaseConnectionUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = "connections_permission"
    model = DatabaseConnection
    form_class = DatabaseConnectionForm
    template_name = "connections/database_connection_form.html"
    success_url = reverse_lazy("explorer_connections")


class DatabaseConnectionDeleteView(PermissionRequiredMixin, DeleteView):
    permission_required = "connections_permission"
    model = DatabaseConnection
    template_name = "connections/database_connection_confirm_delete.html"
    success_url = reverse_lazy("explorer_connections")

    def delete(self, request, *args, **kwargs):
        connection = self.get_object()
        if connection.is_upload:
            delete_from_s3(connection.host)
        return super().delete(request, *args, **kwargs)


class DatabaseConnectionValidateView(PermissionRequiredMixin, View):

    permission_required = "connections_permission"

    def post(self, request):
        form = DatabaseConnectionForm(request.POST)

        instance = DatabaseConnection.objects.filter(alias=request.POST["alias"]).first()
        if instance:
            form = DatabaseConnectionForm(request.POST, instance=instance)
        if form.is_valid():
            connection_data = form.cleaned_data
            explorer_connection = DatabaseConnection(
                alias=connection_data["alias"],
                engine=connection_data["engine"],
                name=connection_data["name"],
                user=connection_data["user"],
                password=connection_data["password"],
                host=connection_data["host"],
                port=connection_data["port"]
            )
            try:
                conn = create_django_style_connection(explorer_connection)
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                return JsonResponse({"success": True})
            except OperationalError as e:
                return JsonResponse({"success": False, "error": str(e)})
        else:
            return JsonResponse({"success": False, "error": "Invalid form data"})
