from django.conf import settings
from django.shortcuts import render

from explorer import app_settings


class ExplorerContextMixin:

    def gen_ctx(self):
        return {
            "can_view": app_settings.EXPLORER_PERMISSION_VIEW(
                self.request
            ),
            "can_change": app_settings.EXPLORER_PERMISSION_CHANGE(
                self.request
            ),
            "can_manage_connections": app_settings.EXPLORER_PERMISSION_CONNECTIONS(
                self.request
            ),
            "assistant_enabled": app_settings.has_assistant(),
            "db_connections_enabled": app_settings.db_connections_enabled(),
            "user_uploads_enabled": app_settings.user_uploads_enabled(),
            "csrf_cookie_name": settings.CSRF_COOKIE_NAME,
            "csrf_token_in_dom": settings.CSRF_COOKIE_HTTPONLY or settings.CSRF_USE_SESSIONS,
            "view_name": self.request.resolver_match.view_name,
        }

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(self.gen_ctx())
        return ctx

    def render_template(self, template, ctx):
        ctx.update(self.gen_ctx())
        return render(self.request, template, ctx)
