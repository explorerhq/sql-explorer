from django.db import connections
from explorer.app_settings import (
    EXPLORER_SCHEMA_INCLUDE_TABLE_PREFIXES,
    EXPLORER_SCHEMA_EXCLUDE_TABLE_PREFIXES
)


# These wrappers make it easy to mock and test
def _get_includes():
    return EXPLORER_SCHEMA_INCLUDE_TABLE_PREFIXES


def _get_excludes():
    return EXPLORER_SCHEMA_EXCLUDE_TABLE_PREFIXES


def _include_table(t):
    if _get_includes() is not None:
        return any([t.startswith(p) for p in _get_includes()])
    return not any([t.startswith(p) for p in _get_excludes()])


def schema_info(connection_alias):
    """
    Construct schema information via engine-specific queries of the tables in the DB.

    :return: Schema information of the following form, sorted by db_table_name.
        [
            ("db_table_name",
                [
                    ("db_column_name", "DbFieldType"),
                    (...),
                ]
            )
        ]

    """
    connection = connections[connection_alias]
    ret = []
    with connection.cursor() as cursor:
        tables_to_introspect = connection.introspection.table_names(cursor)

        for table_name in tables_to_introspect:
            if not _include_table(table_name):
                continue
            td = []
            table_description = connection.introspection.get_table_description(cursor, table_name)
            for row in table_description:
                column_name = row[0]
                try:
                    field_type = connection.introspection.get_field_type(row[1], row)
                except KeyError as e:
                    field_type = 'Unknown'
                td.append((column_name, field_type))
            ret.append((table_name, td))
    return ret
