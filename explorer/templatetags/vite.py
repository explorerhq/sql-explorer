import os

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
from explorer import app_settings, get_version

register = template.Library()

VITE_OUTPUT_DIR = f"{settings.STATIC_URL}explorer/"
VITE_DEV_DIR = "explorer/src/"
VITE_SERVER_HOST = getattr(settings, "VITE_SERVER_HOST", "localhost")
VITE_SERVER_PORT = getattr(settings, "VITE_SERVER_PORT", "5173")


def get_css_link(file: str) -> str:
    if app_settings.VITE_DEV_MODE is False:
        file = file.replace(".scss", ".css")
        base_url = f"{VITE_OUTPUT_DIR}"
    else:
        base_url = f"http://{VITE_SERVER_HOST}:{VITE_SERVER_PORT}/{VITE_DEV_DIR}"
    return mark_safe(f'<link rel="stylesheet" href="{base_url}{file}">')


def get_script(file: str) -> str:
    if app_settings.VITE_DEV_MODE is False:
        file = file.replace(".js", f".{get_version()}.js")
        return mark_safe(f'<script type="module" src="{VITE_OUTPUT_DIR}{file}"></script>')
    else:
        base_url = f"http://{VITE_SERVER_HOST}:{VITE_SERVER_PORT}/{VITE_DEV_DIR}"
    return mark_safe(f'<script type="module" src="{base_url}{file}"></script>')


def get_asset(file: str) -> str:
    if app_settings.VITE_DEV_MODE is False:
        return mark_safe(f"{VITE_OUTPUT_DIR}{file}")
    else:
        return mark_safe(f"http://{VITE_SERVER_HOST}:{VITE_SERVER_PORT}/{VITE_DEV_DIR}{file}")


@register.simple_tag
def vite_asset(filename: str):
    if str(filename).endswith("scss"):
        if app_settings.VITE_DEV_MODE is False:
            filename = os.path.basename(filename)
        return get_css_link(filename)
    if str(filename).endswith("js"):
        if app_settings.VITE_DEV_MODE is False:
            filename = os.path.basename(filename)
        return get_script(filename)

    # Non js/scss assets respect directory structure so don't need to do the filename rewrite
    return get_asset(filename)


@register.simple_tag
def vite_hmr_client():
    if app_settings.VITE_DEV_MODE is False:
        return ""
    base_url = f"http://{VITE_SERVER_HOST}:{VITE_SERVER_PORT}/@vite/client"
    return mark_safe(f'<script type="module" src="{base_url}"></script>')
