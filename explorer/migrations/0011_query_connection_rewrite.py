from django.db import migrations

from explorer.app_settings import EXPLORER_CONNECTIONS


def forward(apps, schema_editor):
    Query = apps.get_model("explorer", "Query")

    reverse_map = {v: k for k, v in EXPLORER_CONNECTIONS.items()}

    for q in Query.objects.all():
        conn = q.connection
        new_conn = reverse_map.get(conn)
        if not new_conn:
            raise Exception(
                f"Query({q.id}) references Django DB connection '{conn}' "
                f"which has no alias defined in EXPLORER_CONNECTIONS."
            )
        if conn == new_conn:
            continue
        q.connection = new_conn
        q.save()


def reverse(apps, schema_editor):
    Query = apps.get_model("explorer", "Query")

    for q in Query.objects.all():
        conn = q.connection
        new_conn = EXPLORER_CONNECTIONS.get(conn)
        if not new_conn:
            raise Exception(
                f"Query({q.id}) references Connection alias '{conn}' "
                f"which has no Django DB connection defined in EXPLORER_CONNECTIONS."
            )
        if conn == new_conn:
            continue
        q.connection = new_conn
        q.save()


class Migration(migrations.Migration):
    dependencies = [
        ('explorer', '0010_sql_required'),
    ]

    operations = [
        migrations.RunPython(forward, reverse),
    ]
