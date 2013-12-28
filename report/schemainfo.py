from django.db import models


def schemainfo():
    ret = []
    for app in models.get_apps():
        for model in models.get_models(app):
            friendly_model = "%s -> %s" % (model._meta.app_label, model._meta.object_name)
            cur_app = (friendly_model, str(model._meta.db_table), [])
            for f in model._meta.fields:
                cur_app[2].append((f.get_attname_column()[1], f.get_internal_type()))
            ret.append(cur_app)
    return ret

