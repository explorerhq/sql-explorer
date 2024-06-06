from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import View

from explorer import app_settings
from explorer.forms import QueryForm
from explorer.models import MSG_FAILED_BLACKLIST, Query, QueryLog
from explorer.utils import (
    url_get_fullscreen, url_get_log_id, url_get_params, url_get_query_id, url_get_rows, url_get_show,
    InvalidExplorerConnectionException
)
from explorer.views.auth import PermissionRequiredMixin
from explorer.views.mixins import ExplorerContextMixin
from explorer.views.utils import query_viewmodel


class PlayQueryView(PermissionRequiredMixin, ExplorerContextMixin, View):
    permission_required = "change_permission"

    def get(self, request):
        if url_get_query_id(request):
            query = get_object_or_404(Query, pk=url_get_query_id(request))
            return self.render_with_sql(request, query, run_query=False)

        if url_get_log_id(request):
            log = get_object_or_404(QueryLog, pk=url_get_log_id(request))
            c = log.connection or ""
            query = Query(sql=log.sql, title="Playground", connection=c)
            return self.render_with_sql(request, query)

        return self.render()

    def post(self, request):
        c = request.POST.get("connection", "")
        show = url_get_show(request)
        sql = request.POST.get("sql", "")

        query = Query(sql=sql, title="Playground", connection=c)

        passes_blacklist, failing_words = query.passes_blacklist()

        error = MSG_FAILED_BLACKLIST % ", ".join(
            failing_words
        ) if not passes_blacklist else None

        run_query = not bool(error) if show else False
        return self.render_with_sql(
            request,
            query,
            run_query=run_query,
            error=error
        )

    def render(self):
        return self.render_template(
            "explorer/play.html",
            {
                "title": "Playground",
                "form": QueryForm()
            }
        )

    def render_with_sql(self, request, query, run_query=True, error=None):
        rows = url_get_rows(request)
        fullscreen = url_get_fullscreen(request)
        template = "fullscreen" if fullscreen else "play"
        form = QueryForm(
            request.POST if len(request.POST) else None,
            instance=query
        )
        return self.render_template(
            f"explorer/{template}.html",
            query_viewmodel(
                request,
                query,
                title="Playground",
                run_query=run_query,
                error=error,
                rows=rows,
                form=form
            )
        )


class QueryView(PermissionRequiredMixin, ExplorerContextMixin, View):
    permission_required = "view_permission"

    def get(self, request, query_id):
        query, form = QueryView.get_instance_and_form(request, query_id)
        query.save()  # updates the modified date
        show = url_get_show(request)
        rows = url_get_rows(request)
        params = query.available_params()
        if not app_settings.EXPLORER_AUTORUN_QUERY_WITH_PARAMS and params:
            show = False
        try:
            vm = query_viewmodel(
                request,
                query,
                form=form,
                run_query=show,
                rows=rows
            )
        except InvalidExplorerConnectionException as e:
            vm = query_viewmodel(
                request,
                query,
                form=form,
                run_query=False,
                error=str(e)
            )
        fullscreen = url_get_fullscreen(request)
        template = "fullscreen" if fullscreen else "query"
        return self.render_template(
            f"explorer/{template}.html", vm
        )

    def post(self, request, query_id):
        if not app_settings.EXPLORER_PERMISSION_CHANGE(request):
            return HttpResponseRedirect(
                reverse_lazy("query_detail", kwargs={"query_id": query_id})
            )
        show = url_get_show(request)
        query, form = QueryView.get_instance_and_form(request, query_id)
        success = form.is_valid() and form.save()
        try:
            vm = query_viewmodel(
                request,
                query,
                form=form,
                run_query=show,
                rows=url_get_rows(request),
                message=_("Query saved.") if success else None
            )
        except ValidationError as ve:
            vm = query_viewmodel(
                request,
                query,
                form=form,
                run_query=False,
                rows=url_get_rows(request),
                error=ve.message
            )
        return self.render_template("explorer/query.html", vm)

    @staticmethod
    def get_instance_and_form(request, query_id):
        query = get_object_or_404(Query.objects.prefetch_related("favorites"), pk=query_id)
        query.params = url_get_params(request)
        form = QueryForm(
            request.POST if len(request.POST) else None,
            instance=query
        )
        return query, form
