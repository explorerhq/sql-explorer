import io
import json
from explorer.ee.db_connections.mime import is_csv, is_json, is_sqlite, is_json_list


MAX_TYPING_SAMPLE_SIZE = 5000
SHORTEST_PLAUSIBLE_DATE_STRING = 5


def get_parser(file):
    if is_csv(file):
        return csv_to_typed_df
    if is_json_list(file):
        return json_list_to_typed_df
    if is_json(file):
        return json_to_typed_df
    if is_sqlite(file):
        return None
    raise ValueError(f"File {file.content_type} not supported.")


def csv_to_typed_df(csv_bytes, delimiter=",", has_headers=True):
    import pandas as pd
    csv_file = io.BytesIO(csv_bytes)
    df = pd.read_csv(csv_file, sep=delimiter, header=0 if has_headers else None)
    return df_to_typed_df(df)


def json_list_to_typed_df(json_bytes):
    import pandas as pd
    data = []
    for line in io.BytesIO(json_bytes).readlines():
        data.append(json.loads(line.decode("utf-8")))

    df = pd.json_normalize(data)
    return df_to_typed_df(df)


def json_to_typed_df(json_bytes):
    import pandas as pd
    json_file = io.BytesIO(json_bytes)
    json_content = json.load(json_file)
    df = pd.json_normalize(json_content)
    return df_to_typed_df(df)


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



def df_to_typed_df(df):  # noqa
    import pandas as pd
    from dateutil import parser
    try:

        for column in df.columns:

            # If we somehow have an array within a field (e.g. from a json object) then convert it to a string
            df[column] = df[column].apply(lambda x: str(x) if isinstance(x, list) else x)

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
