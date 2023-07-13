PII_MASKING_PATTERN_REPLACEMENT_DICT = {
    r"(?:\+?\d{1,3}|0)?([6-9]\d{9})\b": "XXXXXXXXXXX", # For phone number
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b": "XXX@XXX.com", # For email
}

TYPE_CODE_FOR_JSON = 3802
TYPE_CODE_FOR_TEXT = 25