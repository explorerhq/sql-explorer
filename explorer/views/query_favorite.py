from django.http import JsonResponse
from django.views import View

from explorer.models import QueryFavorite
from explorer.views.auth import PermissionRequiredMixin
from explorer.views.mixins import ExplorerContextMixin


class QueryFavoritesView(PermissionRequiredMixin, ExplorerContextMixin, View):
    permission_required = "view_permission"

    def get(self, request):
        favorites = QueryFavorite.objects.filter(user=request.user).select_related("query", "user").order_by(
            "query__title")
        return self.render_template(
            "explorer/query_favorites.html", {"favorites": favorites}
        )


class QueryFavoriteView(PermissionRequiredMixin, ExplorerContextMixin, View):
    permission_required = "view_permission"

    @staticmethod
    def build_favorite_response(user, query_id):
        is_favorite = QueryFavorite.objects.filter(user=user, query_id=query_id).exists()
        data = {
            "status": "success",
            "query_id": query_id,
            "is_favorite": is_favorite
        }
        return data

    def get(self, request, query_id):
        return JsonResponse(QueryFavoriteView.build_favorite_response(request.user, query_id))

    def post(self, request, query_id):
        # toggle favorite
        if QueryFavorite.objects.filter(user=request.user, query_id=query_id).exists():
            QueryFavorite.objects.filter(user=request.user, query_id=query_id).delete()
        else:
            QueryFavorite.objects.get_or_create(user=request.user, query_id=query_id)
        return JsonResponse(QueryFavoriteView.build_favorite_response(request.user, query_id))
