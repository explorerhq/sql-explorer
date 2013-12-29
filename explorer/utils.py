import functools
from report import app_settings
from django.db import models


def passes_blacklist(sql):
    clean = functools.reduce(lambda sql, term: sql.upper().replace(term, ""), app_settings.REPORT_SQL_WHITELIST, sql)
    return not any(write_word in clean.upper() for write_word in app_settings.REPORT_SQL_BLACKLIST)


def safe_cast(val, to_type, default=None):
    try:
        return to_type(val)
    except ValueError:
        return default


def get_int_from_request(request, name, default):
    val = request.GET.get(name, default)
    return safe_cast(val, int, default) if val else val  # handle None defaults


def url_get_rows(request):
    return get_int_from_request(request, 'rows', app_settings.REPORT_DEFAULT_ROWS)


def url_get_report_id(request):
    return get_int_from_request(request, 'report_id', None)


def schema_info():
    ret = []
    for app in [a for a in models.get_apps() if a.__package__ not in app_settings.REPORT_SCHEMA_EXCLUDE_APPS]:
        for model in models.get_models(app):
            friendly_model = "%s -> %s" % (model._meta.app_label, model._meta.object_name)
            cur_app = (friendly_model, str(model._meta.db_table), [])
            for f in model._meta.fields:
                cur_app[2].append((f.get_attname_column()[1], f.get_internal_type()))
            ret.append(cur_app)
    return ret