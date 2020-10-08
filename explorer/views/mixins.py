# -*- coding: utf-8 -*-
from django.shortcuts import render

from explorer import app_settings


class ExplorerContextMixin:

    def gen_ctx(self):
        return {
            'can_view': app_settings.EXPLORER_PERMISSION_VIEW(
                self.request.user
            ),
            'can_change': app_settings.EXPLORER_PERMISSION_CHANGE(
                self.request.user
            )
        }

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(self.gen_ctx())
        return ctx

    def render_template(self, template, ctx):
        ctx.update(self.gen_ctx())
        return render(self.request, template, ctx)
