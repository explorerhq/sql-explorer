# -*- coding: utf-8 -*-
from django.http import JsonResponse
from django.views import View

from explorer.tasks import execute_query
from explorer.views.auth import PermissionRequiredMixin


class EmailCsvQueryView(PermissionRequiredMixin, View):

    permission_required = 'view_permission'

    def post(self, request, query_id, *args, **kwargs):
        if request.is_ajax():
            email = request.POST.get('email', None)
            if email:
                execute_query.delay(query_id, email)
                return JsonResponse(
                    {'message': 'message was sent successfully'}
                )
        return JsonResponse({}, status=403)
