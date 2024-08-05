import os
from io import BytesIO

from explorer.utils import secure_filename
from explorer.ee.db_connections.type_infer import get_parser
from explorer.ee.db_connections.utils import pandas_to_sqlite, uploaded_db_local_path


def get_names(file, append_conn=None, user_id=None):
    s_filename = secure_filename(file.name)
    table_name, _ = os.path.splitext(s_filename)

    # f_name represents the filename of both the sqlite DB on S3, and on the local filesystem.
    # If we are appending to an existing data source, then we re-use the same name.
    # New connections get a new database name.
    if append_conn:
        f_name = os.path.basename(append_conn.name)
    else:
        f_name = f"{table_name}_{user_id}.db"

    return table_name, f_name


def parse_to_sqlite(file, append_conn=None, user_id=None) -> (BytesIO, str):

    table_name, f_name = get_names(file, append_conn, user_id)

    # When appending, make sure the database exists locally so that we can write to it
    if append_conn:
        append_conn.download_sqlite_if_needed()

    df_parser = get_parser(file)
    if df_parser:
        try:
            df = df_parser(file.read())
            local_path = uploaded_db_local_path(f_name)
            f_bytes = pandas_to_sqlite(df, table_name, local_path)
        except Exception as e:  # noqa
            raise ValueError(f"Error while parsing {f_name}: {e}") from e
    else:
        # If it's a SQLite file already, simply cough it up as a BytesIO object
        return BytesIO(file.read()), f_name
    return f_bytes, f_name
