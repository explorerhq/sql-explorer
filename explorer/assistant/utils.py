from dataclasses import dataclass
from explorer import app_settings
from explorer.schema import schema_info
from explorer.models import ExplorerValue, Query
from django.db.utils import OperationalError
from django.db.models.functions import Lower
from django.db.models import Q
from explorer.assistant.models import TableDescription


OPENAI_MODEL = app_settings.EXPLORER_ASSISTANT_MODEL["name"]
ROW_SAMPLE_SIZE = 3
MAX_FIELD_SAMPLE_SIZE = 200  # characters


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


def table_schema(db_connection, table_name):
    schema = schema_info(db_connection)
    s = [table for table in schema if table[0].lower() == table_name.lower()]
    if len(s):
        return s[0][1]


def sample_rows_from_table(connection, table_name):
    """
    Fetches a sample of rows from the specified table and ensures that any field values
    exceeding 200 characters (or bytes) are truncated. This is useful for handling fields
    like "description" that might contain very long strings of text or binary data.
    Truncating these fields prevents issues with displaying or processing overly large values.
    An ellipsis ("...") is appended to indicate that the data has been truncated.

    Args:
        connection: The database connection.
        table_name: The name of the table to sample rows from.

    Returns:
        A list of rows with field values truncated if they exceed 500 characters/bytes.
    """
    cursor = connection.cursor()
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
                elif isinstance(field, (bytes, bytearray)):
                    new_val = "<binary_data>"
                processed_row.append(new_val)
            ret.append(processed_row)

        return ret
    except OperationalError as e:
        return [[str(e)]]


def format_rows_from_table(rows):
    """ Given an array of rows (a list of lists), returns e.g.

AlbumId | Title | ArtistId
1 | For Those About To Rock We Salute You | 1
2 | Let It Rip | 2
3 | Restless and Wild | 2

    """
    return "\n".join([" | ".join([str(item) for item in row]) for row in rows])


def build_system_prompt(flavor):
    bsp = ExplorerValue.objects.get_item(ExplorerValue.ASSISTANT_SYSTEM_PROMPT).value
    bsp += f"\nYou are an expert at writing SQL, specifically for {flavor}, and account for the nuances of this dialect of SQL. You always respond with valid {flavor} SQL."  # noqa
    return bsp


def get_relevant_annotation(db_connection, t):
    return TableDescription.objects.annotate(
        table_name_lower=Lower("table_name")
    ).filter(
        database_connection=db_connection,
        table_name_lower=t.lower()
    ).first()


def get_relevant_few_shots(db_connection, included_tables):
    included_tables_lower = [t.lower() for t in included_tables]

    query_conditions = Q()
    for table in included_tables_lower:
        query_conditions |= Q(sql__icontains=table)

    return Query.objects.annotate(
        sql_lower=Lower("sql")
    ).filter(
        database_connection=db_connection,
        few_shot=True
    ).filter(query_conditions)


def get_few_shot_chunk(db_connection, included_tables):
    included_tables = [t.lower() for t in included_tables]
    few_shot_examples = get_relevant_few_shots(db_connection, included_tables)
    if few_shot_examples:
        return "## Relevant example queries, written by expert SQL analysts ##\n" + "\n\n".join(
            [f"Description: {fs.title} - {fs.description}\nSQL:\n{fs.sql}"
             for fs in few_shot_examples.all()]
        )


@dataclass
class TablePromptData:
    name: str
    schema: list
    sample: list
    annotation: TableDescription

    def render(self):
        fmt_schema = "\n".join([str(field) for field in self.schema])
        ret = f"""## Information for Table '{self.name}' ##

Schema:\n{fmt_schema}

Sample rows:\n{format_rows_from_table(self.sample)}"""
        if self.annotation:
            ret += f"\nUsage Notes:\n{self.annotation.description}"
        return ret


def build_prompt(db_connection, assistant_request, included_tables, query_error=None, sql=None):
    included_tables = [t.lower() for t in included_tables]

    error_chunk = f"## Query Error ##\n{query_error}" if query_error else None
    sql_chunk = f"## Existing User-Written SQL ##\n{sql}" if sql else None
    request_chunk = f"## User's Request to Assistant ##\n{assistant_request}"
    table_chunks = [
        TablePromptData(
            name=t,
            schema=table_schema(db_connection, t),
            sample=sample_rows_from_table(db_connection.as_django_connection(), t),
            annotation=get_relevant_annotation(db_connection, t)
        ).render()
        for t in included_tables
    ]
    few_shot_chunk = get_few_shot_chunk(db_connection, included_tables)

    chunks = [error_chunk, sql_chunk, *table_chunks, few_shot_chunk, request_chunk]

    prompt = {
        "system": build_system_prompt(db_connection.as_django_connection().vendor),
        "user": "\n\n".join([c for c in chunks if c]),
    }
    return prompt
