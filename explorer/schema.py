from collections import defaultdict

from django.db import connections
from django.utils.module_loading import import_string


from . import app_settings


class SchemaBase(object):

    vendor = ''
    sql = ''

    def __init__(self, connection):
        self.connection = connection
        self.cur = connection.cursor()
        self.cur.execute(self.sql)
        self.results = self.cur.fetchall()

    def get(self):
        tables = defaultdict(list)
        for r in self._build():
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
            td = []
            table_description = connection.introspection.get_table_description(cursor, table_name)
            for row in table_description:
                column_name = row[0]
                field_type = connection.introspection.get_field_type(row[1], row)
                td.append((column_name, field_type))

            ret.append((table_name, td))
    return ret

