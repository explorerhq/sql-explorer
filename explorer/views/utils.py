from django.db import DatabaseError
import logging
from explorer import app_settings
from explorer.charts import get_chart
from explorer.models import QueryFavorite
from explorer.schema import schema_json_info


logger = logging.getLogger(__name__)


def query_viewmodel(request, query, title=None, form=None, message=None,
                    run_query=True, error=None,
                    rows=app_settings.EXPLORER_DEFAULT_ROWS):
    """

    :return: Returns the context required for a view
    :rtype: dict
    """
    res = None
    ql = None
    if run_query:
        try:
            res, ql = query.execute_with_logging(request.user)
        except DatabaseError as e:
            error = str(e)
    has_valid_results = not error and res and run_query

    fullscreen_params = request.GET.copy()
    if "fullscreen" not in fullscreen_params:
        fullscreen_params.update({
            "fullscreen": 1
        })
    if "rows" not in fullscreen_params:
        fullscreen_params.update({
            "rows": rows
        })
    if "querylog_id" not in fullscreen_params and ql:
        fullscreen_params.update({
            "querylog_id": ql.id
        })

    user = request.user
    is_favorite = False
    if user.is_authenticated and query.pk:
        is_favorite = QueryFavorite.objects.filter(user=user, query=query).exists()

    charts = {"line_chart_svg": None,
              "bar_chart_svg": None}

    try:
        if app_settings.EXPLORER_CHARTS_ENABLED and has_valid_results:
            charts["line_chart_svg"] = get_chart(res,"line", rows)
            charts["bar_chart_svg"] = get_chart(res,"bar", rows)
    except TypeError as e:
        if ql is not None:
            msg = f"Error generating charts for querylog {ql.id}: {e}"
        else:
            msg = f"Error generating charts for query {query.id}: {e}"
        logger.error(msg)

    ret = {
        "tasks_enabled": app_settings.ENABLE_TASKS,
        "params": query.available_params_w_labels(),
        "title": title,
        "shared": query.shared,
        "query": query,
        "form": form,
        "message": message,
        "error": error,
        "rows": rows,
        "query_id": query.id,
        "data": res.data[:rows] if has_valid_results else None,
        "headers": res.headers if has_valid_results else None,
        "total_rows": len(res.data) if has_valid_results else None,
        "duration": res.duration if has_valid_results else None,
        "has_stats":
            len([h for h in res.headers if h.summary])
            if has_valid_results else False,
        "snapshots": query.snapshots if query.snapshot else [],
        "ql_id": ql.id if ql else None,
        "unsafe_rendering": app_settings.UNSAFE_RENDERING,
        "fullscreen_params": fullscreen_params.urlencode(),
        "charts_enabled": app_settings.EXPLORER_CHARTS_ENABLED,
        "is_favorite": is_favorite,
        "show_sql_by_default": app_settings.EXPLORER_SHOW_SQL_BY_DEFAULT,
        "schema_json": schema_json_info(query.database_connection) if query and query.database_connection else None,
    }
    return {**ret, **charts}
