import os
from io import BytesIO

from explorer.ee.db_connections.type_infer import get_parser
from explorer.ee.db_connections.utils import pandas_to_sqlite


def parse_to_sqlite(file) -> (BytesIO, str):
    f_name = file.name
    f_bytes = file.read()
    df_parser = get_parser(file)
    if df_parser:
        df = df_parser(f_bytes)
        try:
            f_bytes = pandas_to_sqlite(df, local_path=f"{f_name}_tmp_local.db")
        except Exception as e:  # noqa
            raise ValueError(f"Error while parsing {f_name}: {e}") from e
        # replace the previous extension with .db, as it is now a sqlite file
        name, _ = os.path.splitext(f_name)
        f_name = f"{name}.db"
    else:
        return BytesIO(f_bytes), f_name  # if it's a SQLite file already, simply cough it up as a BytesIO object
    return f_bytes, f_name

