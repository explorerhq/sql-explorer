from collections import defaultdict
from django.utils.module_loading import import_string
from explorer.app_settings import (
    EXPLORER_SCHEMA_INCLUDE_TABLE_PREFIXES,
    EXPLORER_SCHEMA_EXCLUDE_TABLE_PREFIXES,
    EXPLORER_SCHEMA_BUILDERS
)


# These wrappers make it easy to mock and test

def _get_includes():
    return EXPLORER_SCHEMA_INCLUDE_TABLE_PREFIXES


def _get_excludes():
    return EXPLORER_SCHEMA_EXCLUDE_TABLE_PREFIXES


class SchemaBase(object):

    vendor = ''
    sql = ''

    def __init__(self, connection):
        self.connection = connection
        self.cur = connection.cursor()
        self.cur.execute(self.sql)
        self.results = self.cur.fetchall()

    def _include_table(self, t):
        if _get_includes() is not None:
            return any([t.startswith(p) for p in _get_includes()])
        return not any([t.startswith(p) for p in _get_excludes()])

    def get(self):
        tables = defaultdict(list)
        for r in self._build():
            if self._include_table(r[0]):
                tables[r[0]].append((r[1], r[2]))

        return sorted(tables.items(), key=lambda x: x[0])

    def _build(self):
        return self.results


class SQLiteSchema(SchemaBase):

    vendor = 'sqlite'
    sql = '''
    SELECT name FROM sqlite_master where type='table';'''

    def _build(self):
        schema = []
        for t in self.results:
            self.cur.execute('pragma table_info(%s);' % t)
            for s in self.cur.fetchall():
                schema.append((t[0], s[1], s[2]))
        return schema


class PostgreSQLSchema(SchemaBase):

    vendor = 'postgresql'
    sql = '''
    WITH table_names as (
      select table_name from information_schema.tables WHERE table_schema = 'public'
    ),
    object_ids as (
      SELECT c.oid, c.relname
      FROM pg_catalog.pg_class c
      LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
      WHERE c.relname in (select * from table_names)
    )

    SELECT
      oids.relname "Table",
      a.attname as "Column",
      pg_catalog.format_type(a.atttypid, a.atttypmod) as "Datatype"
      FROM
      pg_catalog.pg_attribute a
        inner join object_ids oids on oids.oid = a.attrelid
      WHERE
        a.attnum > 0
      AND NOT a.attisdropped;'''


class MySQLSchema(SchemaBase):

    vendor = 'mysql'
    sql = '''
    SELECT TABLE_NAME AS "Table", COLUMN_NAME AS "Column", DATA_TYPE AS "Datatype"
    FROM information_schema.columns WHERE table_schema = 'explorertest';'''


def schema_info(connection):
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

    class_str = dict(EXPLORER_SCHEMA_BUILDERS)[connection.vendor]
    Schema = import_string(class_str)
    if not Schema:
        return []
    return Schema(connection).get()
