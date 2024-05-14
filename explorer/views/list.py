import re
from collections import Counter

from django.forms.models import model_to_dict
from django.views.generic import ListView

from explorer import app_settings
from explorer.models import Query, QueryFavorite, QueryLog
from explorer.utils import allowed_query_pks, url_get_query_id
from explorer.views.auth import PermissionRequiredMixin
from explorer.views.mixins import ExplorerContextMixin


class ListQueryView(PermissionRequiredMixin, ExplorerContextMixin, ListView):
    permission_required = "view_permission_list"
    model = Query

    def recently_viewed(self):
        qll = QueryLog.objects.filter(
            run_by_user=self.request.user, query_id__isnull=False
        ).order_by(
            "-run_at"
        ).select_related("query")

        ret = []
        tracker = []
        for ql in qll:
            if len(ret) == app_settings.EXPLORER_RECENT_QUERY_COUNT:
                break

            if ql.query_id not in tracker:
                ret.append(ql)
                tracker.append(ql.query_id)
        return ret

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object_list"] = self._build_queries_and_headers()
        context["recent_queries"] = self.recently_viewed()
        context["tasks_enabled"] = app_settings.ENABLE_TASKS
        context["vite_dev_mode"] = app_settings.VITE_DEV_MODE
        return context

    def get_queryset(self):
        if app_settings.EXPLORER_PERMISSION_VIEW(self.request):
            qs = (
                Query.objects.prefetch_related(
                    "created_by_user", "querylog_set"
                ).all()
            )
        else:
            qs = (
                Query.objects.prefetch_related(
                    "created_by_user", "querylog_set"
                ).filter(pk__in=allowed_query_pks(self.request.user.id))
            )
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

            lrl = q.last_run_log()
            model_dict.update({
                "is_in_category": headers[header] > 1,
                "collapse_target": collapse_target,
                "created_at": q.created_at,
                "is_header": False,
                "run_count": q.querylog_set.count(),
                "ran_successfully": lrl.success,
                "last_run_at": lrl.run_at,
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
        return QueryLog.objects.filter(**kwargs).all()
