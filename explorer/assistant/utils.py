from explorer import app_settings
from explorer.schema import schema_info
from explorer.models import ExplorerValue
from explorer.utils import get_valid_connection
from django.db.utils import OperationalError


OPENAI_MODEL = app_settings.EXPLORER_ASSISTANT_MODEL["name"]
ROW_SAMPLE_SIZE = 2
MAX_FIELD_SAMPLE_SIZE = 500  # characters


def openai_client():
    from openai import OpenAI
    return OpenAI(
        api_key=app_settings.EXPLORER_AI_API_KEY,
        base_url=app_settings.EXPLORER_ASSISTANT_BASE_URL
    )


def do_req(prompt):
    messages = [
        {"role": "system", "content": prompt["system"]},
        {"role": "user", "content": prompt["user"]},
    ]
    resp = openai_client().chat.completions.create(
      model=OPENAI_MODEL,
      messages=messages
    )
    messages.append(resp.choices[0].message)
    return messages


def extract_response(r):
    return r[-1].content


def tables_from_schema_info(connection, table_names):
    schema = schema_info(connection)
    return [table for table in schema if table[0] in set(table_names)]


def sample_rows_from_tables(connection, table_names):
    ret = ""
    for table_name in table_names:
        ret += f"SAMPLE FROM TABLE {table_name}:\n"
        ret += format_rows_from_table(
            sample_rows_from_table(connection, table_name)
        ) + "\n\n"
    return ret


def sample_rows_from_table(connection, table_name):
    """
    Fetches a sample of rows from the specified table and ensures that any field values
    exceeding 500 characters (or bytes) are truncated. This is useful for handling fields
    like "description" that might contain very long strings of text or binary data.
    Truncating these fields prevents issues with displaying or processing overly large values.
    An ellipsis ("...") is appended to indicate that the data has been truncated.

    Args:
        connection: The database connection.
        table_name: The name of the table to sample rows from.

    Returns:
        A list of rows with field values truncated if they exceed 500 characters/bytes.
    """
    conn = get_valid_connection(connection)
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT * FROM {table_name} LIMIT {ROW_SAMPLE_SIZE}")
        ret = [[header[0] for header in cursor.description]]
        rows = cursor.fetchall()

        for row in rows:
            processed_row = []
            for field in row:
                new_val = field
                if isinstance(field, str) and len(field) > MAX_FIELD_SAMPLE_SIZE:
                    new_val = field[:MAX_FIELD_SAMPLE_SIZE] + "..."  # Truncate and add ellipsis
                elif isinstance(field, (bytes, bytearray)) and len(field) > MAX_FIELD_SAMPLE_SIZE:
                    new_val = field[:MAX_FIELD_SAMPLE_SIZE] + b"..."  # Truncate binary data
                processed_row.append(new_val)
            ret.append(processed_row)

        return ret
    except OperationalError as e:
        return [[str(e)]]


def format_rows_from_table(rows):
    column_headers = list(rows[0])
    ret = " | ".join(column_headers) + "\n" + "-" * 50 + "\n"
    for row in rows[1:]:
        row_str = " | ".join(str(item) for item in row)
        ret += row_str + "\n"
    return ret


def get_table_names_from_query(sql):
    from sql_metadata import Parser
    if sql:
        try:
            parsed = Parser(sql)
            return parsed.tables
        except ValueError:
            return []
    return []


def num_tokens_from_string(string: str) -> int:
    """Returns the number of tokens in a text string."""
    import tiktoken
    try:
        encoding = tiktoken.encoding_for_model(OPENAI_MODEL)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    num_tokens = len(encoding.encode(string))
    return num_tokens


def fits_in_window(string: str) -> bool:
    # Ratchet down by 5% to account for other boilerplate and system prompt
    # TODO make this better by actually looking at the token count of the system prompt
    return num_tokens_from_string(string) < (app_settings.EXPLORER_ASSISTANT_MODEL["max_tokens"] * 0.95)


def build_prompt(request_data, included_tables):
    user_prompt = ""

    db_vendor = get_valid_connection(request_data.get("connection")).vendor
    user_prompt += f"## Database Vendor / SQL Flavor is {db_vendor}\n\n"

    db_error = request_data.get("db_error")
    if db_error:
        user_prompt += f"## Query Error ##\n\n{db_error}\n\n"

    sql = request_data.get("sql")
    if sql:
        user_prompt += f"## Existing SQL ##\n\n{sql}\n\n"

    results_sample = sample_rows_from_tables(request_data["connection"],
                                             included_tables)
    if fits_in_window(user_prompt + results_sample):
        user_prompt += f"## Table Structure with Sampled Data ##\n\n{results_sample}\n\n"
    else:  # If it's too large with sampling, then provide *just* the structure
        table_struct = tables_from_schema_info(request_data["connection"],
                                               included_tables)
        user_prompt += f"## Table Structure ##\n\n{table_struct}\n\n"

    user_prompt += f"## User's Request to Assistant ##\n\n{request_data['assistant_request']}\n\n"

    prompt = {
        "system": ExplorerValue.objects.get_item(ExplorerValue.ASSISTANT_SYSTEM_PROMPT).value,
        "user": user_prompt
    }
    return prompt
