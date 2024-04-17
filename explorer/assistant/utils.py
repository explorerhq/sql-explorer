from explorer import app_settings
from explorer.schema import schema_info
from explorer.utils import get_valid_connection
from sql_metadata import Parser
from django.db.utils import OperationalError

if app_settings.EXPLORER_AI_API_KEY:
    import tiktoken
    from openai import OpenAI

OPENAI_MODEL = app_settings.EXPLORER_ASSISTANT_MODEL["name"]
ROW_SAMPLE_SIZE = 2


def openai_client():
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
        ret = f"SAMPLE FROM TABLE {table_name}:\n"
        ret = ret + format_rows_from_table(
            sample_rows_from_table(connection, table_name)
        ) + "\n\n"
    return ret


def sample_rows_from_table(connection, table_name):
    conn = get_valid_connection(connection)
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT * FROM {table_name} LIMIT {ROW_SAMPLE_SIZE}")
        ret = [[header[0] for header in cursor.description]]
        ret = ret + cursor.fetchall()
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
    if sql:
        try:
            parsed = Parser(sql)
            return parsed.tables
        except ValueError:
            return []
    return []


def num_tokens_from_string(string: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model(OPENAI_MODEL)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def fits_in_window(string: str) -> bool:
    # Ratchet down by 5% to account for other boilerplate and system prompt
    # TODO make this better by actually looking at the token count of the system prompt
    return num_tokens_from_string(string) < (app_settings.EXPLORER_ASSISTANT_MODEL["max_tokens"] * 0.95)
