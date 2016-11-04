SCHEMA_SQL = {
    'postgresql': '''
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
      AND NOT a.attisdropped;''',

    'mysql': '''
    SELECT TABLE_NAME AS "Table", COLUMN_NAME AS "Column", DATA_TYPE AS "Datatype"
    FROM information_schema.columns WHERE table_schema = 'explorertest';'''

}
