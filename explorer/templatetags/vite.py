import json
import os
from functools import lru_cache

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
from explorer import app_settings


register = template.Library()

VITE_OUTPUT_DIR = "/static/explorer/"
VITE_DEV_DIR = "explorer/src/"
VITE_MANIFEST_FILE = os.path.join(os.path.dirname(__file__), "../static/explorer/.vite/manifest.json")
VITE_SERVER_HOST = getattr(settings, "VITE_SERVER_HOST", "localhost")
VITE_SERVER_PORT = getattr(settings, "VITE_SERVER_PORT", "5173")


def get_css_link(file: str) -> str:
    if app_settings.VITE_DEV_MODE is False:
        base_url = f"{VITE_OUTPUT_DIR}"
    else:
        base_url = f"http://{VITE_SERVER_HOST}:{VITE_SERVER_PORT}/{VITE_DEV_DIR}"
    return mark_safe(f'<link rel="stylesheet" href="{base_url}{file}">')  # nosec B308, B703


def get_script(file: str) -> str:
    if app_settings.VITE_DEV_MODE is False:
        return mark_safe(f'<script type="module" src="{VITE_OUTPUT_DIR}{file}"></script>')  # nosec B308, B703
    else:
        base_url = f"http://{VITE_SERVER_HOST}:{VITE_SERVER_PORT}/{VITE_DEV_DIR}"
    return mark_safe(f'<script type="module" src="{base_url}{file}"></script>')  # nosec B308, B703


@lru_cache
def get_manifest():
    with open(VITE_MANIFEST_FILE) as f:
        content = f.read()
        manifest = json.loads(content)
        return manifest


@register.simple_tag
def vite_asset(filename: str):
    is_css = str(filename).endswith("css")
    if app_settings.VITE_DEV_MODE is True:
        if is_css is True:
            return get_css_link(filename)
        return get_script(filename)
    manifest = get_manifest()
    full_filename = f"{VITE_DEV_DIR}{filename}"
    file_data = manifest.get(full_filename)
    if file_data is None:
        raise Exception(f'The vite asset "{full_filename}" was not found in the manifest file {VITE_MANIFEST_FILE}.')

    filename = file_data["file"]
    if is_css is True:
        return get_css_link(filename)
    return get_script(filename)


@register.simple_tag
def vite_hmr_client():
    if app_settings.VITE_DEV_MODE is False:
        return ""
    base_url = f"http://{VITE_SERVER_HOST}:{VITE_SERVER_PORT}/@vite/client"
    return mark_safe(f'<script type="module" src="{base_url}"></script>')  # nosec B308, B703
