from django.http import JsonResponse
from django.views import View

from explorer.tasks import execute_query
from explorer.views.auth import PermissionRequiredMixin


class EmailCsvQueryView(PermissionRequiredMixin, View):

    permission_required = "view_permission"

    def post(self, request, query_id, *args, **kwargs):
        email = request.POST.get("email", None)
        if not email:
            return JsonResponse(
                {"error": "email is required"},
                status=400,
            )

        execute_query.delay(query_id, email)

        return JsonResponse({"message": "message was sent successfully"})
