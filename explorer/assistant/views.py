from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
import json

from explorer.tracker import Stat, StatNames
from explorer.utils import get_valid_connection
from explorer.assistant.models import PromptLog
from explorer.assistant.prompts import primary_prompt
from explorer.assistant.utils import (
    do_req, extract_response, tables_from_schema_info,
    get_table_names_from_query, sample_rows_from_tables,
    fits_in_window
)


def run_assistant(request_data, user):

    user_prompt = ""

    db_vendor = get_valid_connection(request_data.get("connection")).vendor
    user_prompt += f"## Database Vendor / SQL Flavor is {db_vendor}\n\n"

    db_error = request_data.get("db_error")
    if db_error:
        user_prompt += f"## Query Error ##\n\n{db_error}\n\n"

    sql = request_data.get("sql")
    if sql:
        user_prompt += f"## Existing SQL ##\n\n{sql}\n\n"

    extra_tables = request_data.get("selected_tables", [])
    included_tables = get_table_names_from_query(sql) + extra_tables
    if included_tables:
        table_struct = tables_from_schema_info(request_data["connection"],
                                               included_tables)
        user_prompt += f"## Relevant Tables' Structure ##\n\n{table_struct}\n\n"

    if fits_in_window(user_prompt):
        results_sample = sample_rows_from_tables(request_data["connection"],
                                                 included_tables)
        if fits_in_window(user_prompt + results_sample):
            user_prompt += f"## Sample Results from Tables ##\n\n{results_sample}\n\n"

    user_prompt += f"## User's Request to Assistant ##\n\n{request_data['assistant_request']}\n\n"

    prompt = primary_prompt.copy()
    prompt["user"] = user_prompt

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


@require_POST
def assistant_help(request):
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
