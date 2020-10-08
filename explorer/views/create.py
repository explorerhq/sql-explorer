# -*- coding: utf-8 -*-
from django.views.generic import CreateView

from explorer.forms import QueryForm
from explorer.views.auth import PermissionRequiredMixin
from explorer.views.mixins import ExplorerContextMixin


class CreateQueryView(PermissionRequiredMixin, ExplorerContextMixin,
                      CreateView):

    permission_required = 'change_permission'
    form_class = QueryForm
    template_name = 'explorer/query.html'

    def form_valid(self, form):
        form.instance.created_by_user = self.request.user
        return super().form_valid(form)
