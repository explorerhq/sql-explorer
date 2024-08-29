from django.http import JsonResponse
from django.views import View
from django.utils import timezone
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy

from .forms import TableDescriptionForm
from .models import TableDescription

import json

from explorer.views.auth import PermissionRequiredMixin
from explorer.views.mixins import ExplorerContextMixin
from explorer.telemetry import Stat, StatNames
from explorer.ee.db_connections.models import DatabaseConnection
from explorer.assistant.models import PromptLog
from explorer.assistant.utils import (
    do_req, extract_response,
    build_prompt
)


def run_assistant(request_data, user):

    sql = request_data.get("sql")
    included_tables = request_data.get("selected_tables", [])

    connection_id = request_data.get("connection_id")
    try:
        conn = DatabaseConnection.objects.get(id=connection_id)
    except DatabaseConnection.DoesNotExist:
        return "Error: Connection not found"
    assistant_request = request_data.get("assistant_request")
    prompt = build_prompt(conn, assistant_request,
                          included_tables, request_data.get("db_error"), request_data.get("sql"))

    start = timezone.now()
    pl = PromptLog(
        prompt=prompt,
        run_by_user=user,
        run_at=timezone.now(),
        user_request=assistant_request,
        database_connection=conn
    )
    response_text = None
    try:
        resp = do_req(prompt)
        response_text = extract_response(resp)
        pl.response = response_text
    except Exception as e:
        pl.error = str(e)
    finally:
        stop = timezone.now()
        pl.duration = (stop - start).total_seconds()
        pl.save()
        Stat(StatNames.ASSISTANT_RUN, {
            "included_table_count": len(included_tables),
            "has_sql": bool(sql),
            "duration": pl.duration,
        }).track()
    return response_text


class AssistantHelpView(View):

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            resp = run_assistant(data, request.user)
            response_data = {
                "status": "success",
                "message": resp
            }
            return JsonResponse(response_data)
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)


class TableDescriptionListView(PermissionRequiredMixin, ExplorerContextMixin, ListView):
    model = TableDescription
    permission_required = "view_permission"
    template_name = "assistant/table_description_list.html"
    context_object_name = "table_descriptions"


class TableDescriptionCreateView(PermissionRequiredMixin, ExplorerContextMixin, CreateView):
    model = TableDescription
    permission_required = "change_permission"
    template_name = "assistant/table_description_form.html"
    success_url = reverse_lazy("table_description_list")
    form_class = TableDescriptionForm


class TableDescriptionUpdateView(PermissionRequiredMixin, ExplorerContextMixin, UpdateView):
    model = TableDescription
    permission_required = "change_permission"
    template_name = "assistant/table_description_form.html"
    success_url = reverse_lazy("table_description_list")
    form_class = TableDescriptionForm


class TableDescriptionDeleteView(PermissionRequiredMixin, ExplorerContextMixin, DeleteView):
    model = TableDescription
    permission_required = "change_permission"
    template_name = "assistant/table_description_confirm_delete.html"
    success_url = reverse_lazy("table_description_list")


class AssistantHistoryApiView(View):

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            logs = PromptLog.objects.filter(
                run_by_user=request.user,
                database_connection_id=data["connection_id"]
            ).order_by("-run_at")[:5]
            ret = [{
                "user_request": log.user_request,
                "response": log.response
            } for log in logs]
            return JsonResponse({"logs": ret})
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
