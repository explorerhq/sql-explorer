from django.http import JsonResponse
from django.views import View
from django.utils import timezone
import json

from explorer.telemetry import Stat, StatNames
from explorer.assistant.models import PromptLog
from explorer.assistant.utils import (
    do_req, extract_response,
    get_table_names_from_query,
    build_prompt
)


def run_assistant(request_data, user):

    sql = request_data.get("sql")
    extra_tables = request_data.get("selected_tables", [])
    included_tables = get_table_names_from_query(sql) + extra_tables

    prompt = build_prompt(request_data, included_tables)

    start = timezone.now()
    pl = PromptLog(
        prompt=prompt,
        run_by_user=user,
        run_at=timezone.now(),
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
            "extra_table_count": len(extra_tables),
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
