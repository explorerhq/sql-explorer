import re
from collections import Counter

from django.db.models import Count, Max, OuterRef, Q, Subquery
from django.forms.models import model_to_dict
from django.views.generic import ListView

from explorer import app_settings
from explorer.models import Query, QueryFavorite, QueryLog
from explorer.utils import allowed_query_pks, get_int_from_request, url_get_query_id
from explorer.views.auth import PermissionRequiredMixin
from explorer.views.mixins import ExplorerContextMixin
from explorer.ee.db_connections.models import DatabaseConnection


class ListQueryView(PermissionRequiredMixin, ExplorerContextMixin, ListView):
    permission_required = "view_permission_list"
    model = Query

    def recently_viewed(self):
        # The most recent run of each of the user's N most recently run queries. Done in the database: iterating the
        # user's logs in Python loaded every one of them, which got slow as logs accumulated.
        latest_runs = (
            QueryLog.objects.filter(run_by_user=self.request.user, query_id__isnull=False)
            .values("query_id")
            .annotate(last_run_at=Max("run_at"))
            .order_by("-last_run_at")[:app_settings.EXPLORER_RECENT_QUERY_COUNT]
        )
        latest_runs = list(latest_runs)
        if not latest_runs:
            return []
        match = Q()
        for run in latest_runs:
            match |= Q(query_id=run["query_id"], run_at=run["last_run_at"])
        logs = {
            ql.query_id: ql
            for ql in QueryLog.objects.filter(match, run_by_user=self.request.user).select_related("query")
        }
        return [logs[run["query_id"]] for run in latest_runs if run["query_id"] in logs]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object_list"] = self._build_queries_and_headers()
        context["connection_count"] = DatabaseConnection.objects.count()
        context["recent_queries"] = self.recently_viewed()
        context["tasks_enabled"] = app_settings.ENABLE_TASKS
        context["vite_dev_mode"] = app_settings.VITE_DEV_MODE
        return context

    def get_queryset(self):
        # Run counts and the last run are computed in the database rather than by prefetching every QueryLog, which
        # loaded the entire log history into memory on each page view.
        last_log = QueryLog.objects.filter(query=OuterRef("pk")).order_by("-run_at")
        qs = Query.objects.select_related("created_by_user", "database_connection").annotate(
            run_count=Count("querylog"),
            last_run_at=Subquery(last_log.values("run_at")[:1]),
            last_run_success=Subquery(last_log.values("success")[:1]),
        ).order_by("title")  # Meta.ordering isn't applied once the query has an aggregate
        if not app_settings.EXPLORER_PERMISSION_VIEW(self.request):
            qs = qs.filter(pk__in=allowed_query_pks(self.request.user.id))
        return qs

    def _build_queries_and_headers(self):
        """
        Build a list of query information and headers (pseudo-folders) for
        consumption by the template.

        Strategy: Look for queries with titles of the form "something - else"
                  (eg. with a ' - ' in the middle) and split on the ' - ',
                  treating the left side as a "header" (or folder).
                  Interleave the headers into the ListView's object_list as
                  appropriate. Ignore headers that only have one child.
                  The front end uses bootstrap's JS Collapse plugin, which
                  necessitates generating CSS classes to map the header onto
                  the child rows, hence the collapse_target variable.

                  To make the return object homogeneous, convert the
                  object_list models into dictionaries for interleaving with
                  the header "objects". This necessitates special handling of
                  'created_at' and 'created_by_user' because model_to_dict
                  doesn't include non-editable fields (created_at) and will
                  give the int representation of the user instead of the
                  string representation.

        :return: A list of model dictionaries representing all the query
                 objects, interleaved with header dictionaries.
        :rtype: list
        """

        dict_list = []
        rendered_headers = []
        pattern = re.compile(r"[\W_]+")

        headers = Counter([q.title.split(" - ")[0] for q in self.object_list])
        query_favorites_for_user = QueryFavorite.objects.filter(user_id=self.request.user.pk).values_list("query_id",
                                                                                                          flat=True)

        for q in self.object_list:
            model_dict = model_to_dict(q)
            header = q.title.split(" - ")[0]
            collapse_target = pattern.sub("", header)

            if headers[header] > 1 and header not in rendered_headers:
                dict_list.append({
                    "title": header,
                    "is_header": True,
                    "is_in_category": False,
                    "collapse_target": collapse_target,
                    "count": headers[header]
                })
                rendered_headers.append(header)

            model_dict.update({
                "is_in_category": headers[header] > 1,
                "collapse_target": collapse_target,
                "created_at": q.created_at,
                "is_header": False,
                "run_count": q.run_count,
                "connection_name": str(q.database_connection),
                # Matches Query.last_run_log(): a never-run query shows its creation time as a successful "run"
                "ran_successfully": q.last_run_success if q.last_run_at else True,
                "last_run_at": q.last_run_at or q.created_at,
                "created_by_user":
                    str(q.created_by_user) if q.created_by_user else None,
                "is_favorite": q.id in query_favorites_for_user
            })
            dict_list.append(model_dict)
        return dict_list


class ListQueryLogView(PermissionRequiredMixin, ExplorerContextMixin, ListView):
    context_object_name = "recent_logs"
    model = QueryLog
    paginate_by = 20
    permission_required = "view_permission"

    def get_queryset(self):
        kwargs = {"sql__isnull": False}
        if url_get_query_id(self.request):
            kwargs["query_id"] = url_get_query_id(self.request)
        connection_id = get_int_from_request(self.request, "connection", None)
        if connection_id:
            kwargs["database_connection_id"] = connection_id
        if self.request.GET.get("run_by_me") and self.request.user.is_authenticated:
            kwargs["run_by_user"] = self.request.user
        return QueryLog.objects.filter(**kwargs).select_related("run_by_user", "database_connection")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        if "page" in params:
            del params["page"]
        context["database_connections"] = DatabaseConnection.objects.all()
        context["selected_connection"] = get_int_from_request(self.request, "connection", None)
        context["run_by_me"] = bool(self.request.GET.get("run_by_me"))
        context["query_id"] = url_get_query_id(self.request)
        context["filter_querystring"] = params.urlencode()
        return context
