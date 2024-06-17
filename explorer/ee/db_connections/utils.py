from django.db import DatabaseError
from django.db.utils import load_backend
import os

from dateutil import parser

import pandas as pd
import sqlite3
import io


# Uploading the same filename twice (from the same user) will overwrite the 'old' DB on S3
def upload_sqlite(db_bytes, path):
    from explorer.utils import get_s3_bucket
    bucket = get_s3_bucket()
    bucket.put_object(Key=path, Body=db_bytes, ServerSideEncryption="AES256")


# Aliases have the user_id appended to them so that if two users upload files with the same name
# they don't step on one another. Without this, the *files* would get uploaded separately (because
# the DBs go into user-specific folders on s3), but the *aliases* would be the same. So one user
# could (innocently) upload a file with the same name, and any existing queries would be suddenly pointing
# to this new database connection. Oops!
# TODO: In the future, queries should probably be FK'ed to the ID of the connection, rather than simply
#       storing the alias of the connection as a string.
def create_connection_for_uploaded_sqlite(filename, user_id, s3_path):
    from explorer.models import DatabaseConnection
    base, ext = os.path.splitext(filename)
    filename = f"{base}_{user_id}{ext}"
    return DatabaseConnection.objects.create(
        alias=f"{filename}",
        engine=DatabaseConnection.SQLITE,
        name=filename,
        host=s3_path
    )


def get_sqlite_for_connection(explorer_connection):
    from explorer.utils import get_s3_bucket

    # Get the database from s3, then modify the connection to work with the downloaded file.
    # E.g. "host" should not be set, and we need to get the full path to the file
    local_name = explorer_connection.local_name
    if not os.path.exists(local_name):
        s3 = get_s3_bucket()
        s3.download_file(explorer_connection.host, local_name)
    explorer_connection.host = None
    explorer_connection.name = local_name
    return explorer_connection


def user_dbs_local_dir():
    d = os.path.normpath(os.path.join(os.getcwd(), "user_dbs"))
    if not os.path.exists(d):
        os.makedirs(d)
    return d


def create_django_style_connection(explorer_connection):

    if explorer_connection.is_upload:
        explorer_connection = get_sqlite_for_connection(explorer_connection)

    connection_settings = {
        "ENGINE": explorer_connection.engine,
        "NAME": explorer_connection.name,
        "USER": explorer_connection.user,
        "PASSWORD": explorer_connection.password,
        "HOST": explorer_connection.host,
        "PORT": explorer_connection.port,
        "TIME_ZONE": None,
        "CONN_MAX_AGE": 0,
        "CONN_HEALTH_CHECKS": False,
        "OPTIONS": {},
        "TEST": {},
        "AUTOCOMMIT": True,
        "ATOMIC_REQUESTS": False,
    }

    try:
        backend = load_backend(explorer_connection.engine)
        return backend.DatabaseWrapper(connection_settings, explorer_connection.alias)
    except DatabaseError as e:
        raise DatabaseError(f"Failed to create explorer connection: {e}") from e


def pandas_to_sqlite(df, local_path="local_database.db"):
    # Write the DataFrame to a local SQLite database
    # In theory, it would be nice to write the dataframe to an in-memory SQLite DB, and then dump the bytes from that
    # but there is no way to get to the underlying bytes from an in-memory SQLite DB
    con = sqlite3.connect(local_path)
    try:
        df.to_sql(name="data", con=con, if_exists="replace", index=False)
    finally:
        con.close()

    # Read the local SQLite database file into a BytesIO buffer
    try:
        db_file = io.BytesIO()
        with open(local_path, "rb") as f:
            db_file.write(f.read())
        db_file.seek(0)
        return db_file
    finally:
        # Delete the local SQLite database file
        # Finally block to ensure we don't litter files around
        os.remove(local_path)


MAX_TYPING_SAMPLE_SIZE = 10000
SHORTEST_PLAUSIBLE_DATE_STRING = 5


def atof_custom(value):
    # Remove any thousands separators and convert the decimal point
    if "," in value and "." in value:
        if value.index(",") < value.index("."):
            # 0,000.00 format
            value = value.replace(",", "")
        else:
            # 0.000,00 format
            value = value.replace(".", "").replace(",", ".")
    elif "," in value:
        # No decimal point, only thousands separator
        value = value.replace(",", "")
    return float(value)

def csv_to_typed_df(csv_bytes, delimiter=",", has_headers=True):  # noqa
    try:

        csv_file = io.BytesIO(csv_bytes)
        df = pd.read_csv(csv_file, sep=delimiter, header=0 if has_headers else None)

        for column in df.columns:
            values = df[column].dropna().unique()
            if len(values) > MAX_TYPING_SAMPLE_SIZE:
                values = pd.Series(values).sample(MAX_TYPING_SAMPLE_SIZE, random_state=42).to_numpy()

            is_date = False
            is_integer = True
            is_float = True

            for value in values:
                try:
                    float_val = atof_custom(str(value))
                    if float_val == int(float_val):
                        continue  # This is effectively an integer
                    else:
                        is_integer = False
                except ValueError:
                    is_integer = False
                    is_float = False
                    break

            if is_integer:
                is_float = False

            if not is_integer and not is_float:
                is_date = True

                # The dateutil parser is very aggressive and will interpret many short strings as dates.
                # For example "12a" will be interpreted as 12:00 AM on the current date.
                # That is not the behavior anyone wants. The shortest plausible date string is e.g. 1-1-23
                try_parse = [v for v in values if len(str(v)) > SHORTEST_PLAUSIBLE_DATE_STRING]
                if len(try_parse) > 0:
                    for value in try_parse:
                        try:
                            parser.parse(str(value))
                        except (ValueError, TypeError, OverflowError):
                            is_date = False
                            break
                else:
                    is_date = False

            if is_date:
                df[column] = pd.to_datetime(df[column], errors="coerce", utc=True)
            elif is_integer:
                df[column] = df[column].apply(lambda x: int(atof_custom(str(x))) if pd.notna(x) else x)
                # If there are NaN / blank values, the column will be converted to float
                # Convert it back to integer
                df[column] = df[column].astype("Int64")
            elif is_float:
                df[column] = df[column].apply(lambda x: atof_custom(str(x)) if pd.notna(x) else x)
            else:
                inferred_type = pd.api.types.infer_dtype(values)
                if inferred_type == "integer":
                    df[column] = pd.to_numeric(df[column], errors="coerce", downcast="integer")
                elif inferred_type == "floating":
                    df[column] = pd.to_numeric(df[column], errors="coerce")

        return df

    except pd.errors.ParserError as e:
        return str(e)


def is_csv(file):
    return file.content_type == "text/csv"
