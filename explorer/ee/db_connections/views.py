import logging
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.views import View
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy
from django.db.utils import OperationalError, DatabaseError
from explorer.models import DatabaseConnection
from explorer.ee.db_connections.utils import (
    upload_sqlite,
    create_connection_for_uploaded_sqlite
)
from explorer.ee.db_connections.create_sqlite import parse_to_sqlite
from explorer.schema import clear_schema_cache
from explorer.app_settings import EXPLORER_MAX_UPLOAD_SIZE
from explorer.ee.db_connections.forms import DatabaseConnectionForm
from explorer.utils import delete_from_s3
from explorer.views.auth import PermissionRequiredMixin
from explorer.views.mixins import ExplorerContextMixin
from explorer.ee.db_connections.mime import is_sqlite


logger = logging.getLogger(__name__)


class UploadDbView(PermissionRequiredMixin, View):

    permission_required = "connections_permission"

    def post(self, request):  # noqa
        file = request.FILES.get("file")
        if file:

            # 'append' should be None, or the ID of the DatabaseConnection to append this table to.
            # This is stored in DatabaseConnection.host of the previously uploaded connection
            append = request.POST.get("append")
            append_path = None
            conn = None
            if append:
                conn = DatabaseConnection.objects.get(id=append)
                append_path = conn.host

            if file.size > EXPLORER_MAX_UPLOAD_SIZE:
                friendly = EXPLORER_MAX_UPLOAD_SIZE / (1024 * 1024)
                return JsonResponse({"error": f"File size exceeds the limit of {friendly} MB"}, status=400)

            # You can't double stramp a triple stamp!
            if append_path and is_sqlite(file):
                msg = "Can't append a SQLite file to a SQLite file. Only CSV and JSON."
                logger.error(msg)
                return JsonResponse({"error": msg}, status=400)

            try:
                f_bytes, f_name = parse_to_sqlite(file, conn, request.user.id)
            except ValueError as e:
                logger.error(f"Error getting bytes for {file.name}: {e}")
                return JsonResponse({"error": "File was not csv, json, or sqlite."}, status=400)
            except TypeError as e:
                logger.error(f"Error parse {file.name}: {e}")
                return JsonResponse({"error": "Error parsing file."}, status=400)

            if append_path:
                s3_path = append_path
            else:
                s3_path = f"user_dbs/user_{request.user.id}/{f_name}"

            try:
                upload_sqlite(f_bytes, s3_path)
            except Exception as e:  # noqa
                logger.exception(f"Exception while uploading file {f_name}: {e}")
                return JsonResponse({"error": "Error while uploading file to S3."}, status=400)

            # If we're not appending, then need to create a new DatabaseConnection
            if not append_path:
                conn = create_connection_for_uploaded_sqlite(f_name, s3_path)

            clear_schema_cache(conn)
            conn.update_fingerprint()
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"error": "No file provided"}, status=400)


class DatabaseConnectionsListView(PermissionRequiredMixin, ExplorerContextMixin, ListView):

    permission_required = "connections_permission"
    template_name = "connections/connections.html"
    model = DatabaseConnection


class DatabaseConnectionDetailView(PermissionRequiredMixin, ExplorerContextMixin, DetailView):
    permission_required = "connections_permission"
    model = DatabaseConnection
    template_name = "connections/database_connection_detail.html"


class DatabaseConnectionCreateView(PermissionRequiredMixin, ExplorerContextMixin, CreateView):
    permission_required = "connections_permission"
    model = DatabaseConnection
    form_class = DatabaseConnectionForm
    template_name = "connections/database_connection_form.html"
    success_url = reverse_lazy("explorer_connections")


class DatabaseConnectionUploadCreateView(TemplateView):
    template_name = "connections/connection_upload.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["valid_connections"] = DatabaseConnection.objects.filter(engine=DatabaseConnection.SQLITE,
                                                                         host__isnull=False)
        return context


class DatabaseConnectionUpdateView(PermissionRequiredMixin, ExplorerContextMixin, UpdateView):
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


class DatabaseConnectionRefreshView(PermissionRequiredMixin, View):

    permission_required = "connections_permission"
    success_url = reverse_lazy("explorer_connections")

    def get(self, request, pk):  # noqa
        conn = DatabaseConnection.objects.get(id=pk)
        conn.delete_local_sqlite()
        clear_schema_cache(conn)
        message = f"Deleted schema cache for {conn.alias}. Schema will be regenerated on next use."
        if conn.is_upload:
            message += "\nRemoved local SQLite DB. Will be re-downloaded from S3 on next use."
        message += "\nPlease hit back to return to the application."
        return HttpResponse(content_type="text/plain", content=message)


class DatabaseConnectionValidateView(PermissionRequiredMixin, View):

    permission_required = "connections_permission"

    # pk param is ignored, in order to deal with having 2 URL patterns
    def post(self, request, pk=None):  # noqa
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
                port=connection_data["port"],
                extras=connection_data["extras"]
            )
            try:
                conn = explorer_connection.as_django_connection()
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                return JsonResponse({"success": True})
            except OperationalError as e:
                return JsonResponse({"success": False, "error": str(e)})
            except DatabaseError as e:
                return JsonResponse({"success": False, "error": str(e)})
        else:
            return JsonResponse({"success": False, "error": "Invalid form data"})
