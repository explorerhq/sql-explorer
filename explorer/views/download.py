from django.shortcuts import get_object_or_404
from django.views.generic.base import View

from explorer.models import Query
from explorer.views.auth import PermissionRequiredMixin
from explorer.views.export import _export
from explorer.ee.db_connections.utils import default_db_connection_id


class DownloadQueryView(PermissionRequiredMixin, View):

    permission_required = "view_permission"

    def get(self, request, query_id, *args, **kwargs):
        query = get_object_or_404(Query, pk=query_id)
        return _export(request, query)


class DownloadFromSqlView(PermissionRequiredMixin, View):

    permission_required = "view_permission"

    def post(self, request, *args, **kwargs):
        sql = request.POST.get("sql", "")
        connection = request.POST.get("database_connection", default_db_connection_id())
        query = Query(sql=sql, database_connection_id=connection, title="")
        ql = query.log(request.user)
        query.title = f"Playground-{ql.id}"
        return _export(request, query)
