from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View

from explorer.models import Query, QueryFavorite
from explorer.views.auth import PermissionRequiredMixin
from explorer.views.mixins import ExplorerContextMixin


class QueryFavoritesView(PermissionRequiredMixin, ExplorerContextMixin, View):
    permission_required = 'view_permission'

    def get(self, request):
        user = request.user
        favorites = QueryFavorite.objects.filter(user=user).select_related('user').select_related('query').order_by(
            'query__title')
        return self.render_template(
            'explorer/query_favorites.html', {'favorites': favorites}
        )


class QueryFavoriteView(PermissionRequiredMixin, ExplorerContextMixin, View):
    permission_required = 'view_permission'

    @staticmethod
    def build_favorite_response(user, query):
        is_favorite = QueryFavorite.objects.filter(user=user, query=query).exists()
        data = {
            'status': 'success',
            'query_id': query.id,
            'is_favorite': is_favorite
        }
        return data

    def get(self, request, query_id):
        user = request.user
        query = get_object_or_404(Query, pk=query_id)
        return JsonResponse(QueryFavoriteView.build_favorite_response(user, query))

    def post(self, request, query_id):
        # toggle favorite
        user = request.user
        query = get_object_or_404(Query, pk=query_id)
        if QueryFavorite.objects.filter(user=user, query=query).exists():
            QueryFavorite.objects.filter(user=user, query=query).delete()
        else:
            QueryFavorite.objects.get_or_create(user=user, query=query)
        return JsonResponse(QueryFavoriteView.build_favorite_response(user, query))
