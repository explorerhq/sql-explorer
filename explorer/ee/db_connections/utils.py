from django.db import DatabaseError
from django.db.utils import load_backend
import os
import json

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

    if explorer_connection.extras:
        extras_dict = json.loads(explorer_connection.extras) if isinstance(explorer_connection.extras,
                                                                           str) else explorer_connection.extras
        connection_settings.update(extras_dict)

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
