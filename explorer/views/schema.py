from django.http import Http404, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.clickjacking import xframe_options_sameorigin
from explorer.ee.db_connections.models import DatabaseConnection
from explorer.ee.db_connections.utils import default_db_connection_id

from explorer.schema import schema_info, schema_json_info
from explorer.views.auth import PermissionRequiredMixin


class SchemaView(PermissionRequiredMixin, View):

    permission_required = "change_permission"

    @method_decorator(xframe_options_sameorigin)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        connection_id = kwargs.get("connection", default_db_connection_id())
        try:
            connection = DatabaseConnection.objects.get(id=connection_id)
        except DatabaseConnection.DoesNotExist as e:
            raise Http404 from e
        except ValueError as e:
            raise Http404 from e
        schema = schema_info(connection)
        if schema:
            return render(
                request,
                "explorer/schema.html",
                {"schema": schema}
            )
        else:
            return render(request,
                          "explorer/schema_error.html",
                          {"connection": connection.alias})


class SchemaJsonView(PermissionRequiredMixin, View):

    permission_required = "change_permission"

    def get(self, request, *args, **kwargs):
        connection = kwargs.get("connection", default_db_connection_id())
        conn = get_object_or_404(DatabaseConnection, id=connection)
        return JsonResponse(schema_json_info(conn))
