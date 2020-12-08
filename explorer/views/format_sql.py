# -*- coding: utf-8 -*-
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from explorer.utils import fmt_sql


@require_POST
def format_sql(request):
    sql = request.POST.get('sql', '')
    formatted = fmt_sql(sql)
    return JsonResponse({"formatted": formatted})
