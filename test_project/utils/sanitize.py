# -*- coding: utf-8 -*-
"""
.. module:: test_project.utils.sanitize
   :synopsis: Utility function to sanitize values to required output types.

.. moduleauthor:: Mark Walker
"""

# pylint: disable=inconsistent-return-statements


def sanitize(value, output_type):
    """
    Handy wrapper function for individual sanitize functions.

    :param value: Input value to be sanitized
    :param output_type: Class of required output
    :type output_type: bool or int
    """
    # pylint: disable=no-else-return

    if output_type == bool:
        return sanitize_bool(value)
    elif output_type == int:
        return sanitize_int(value)
    # pylint: enable=no-else-return
    # unrecognised/unsupported output_type. just return what we got..
    return value


def sanitize_int(value):
    """
    Sanitize an input value to an integer.

    :param value: Input value to be sanitized to an integer
    :return: Integer, or None of the value cannot be sanitized
    :rtype: int or None
    """
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    elif isinstance(value, int):
        return value

# pylint: enable=inconsistent-return-statements


def sanitize_bool(value, strict=False):
    """
    Sanitize an input value to a boolean

    :param value: Input value to be sanitized to a boolean
    :param strict: if strict, if the value is not directly recognised as a
                    yes/no bool, we'll return None...if not strict, we'll
                    convert the unknown value to bool() and return True/False
    :return: Boolean representation of input value.
    :rtype: bool or NoneType
    """
    if isinstance(value, str):
        # pylint: disable=no-else-return
        if value.lower().strip() in {'y', 'yes', 't', 'true', '1'}:
            return True
        elif value.lower().strip() in {'n', 'no', 'f', 'false', '0'}:
            return False
        else:
            int_value = sanitize_int(value)
            if int_value is not None:
                return int_value > 0

            return False
        # pylint: enable=no-else-return

    # Bool compare before int compare. This is because True isinstance() check
    # will relate to 1 which means isinstance(value, int) will result as True,
    # whilst being a bool. Testing a number against bool will result in False,
    # therefore order is very important.
    elif isinstance(value, bool):
        return value
    elif isinstance(value, int):
        return value > 0

    # list of one (how formbuilder tends to store single checkbox choices)
    if isinstance(value, (list, tuple)) and len(value) == 1:
        # recurse
        return sanitize_bool(value[0], strict=strict)

    if strict:
        return None

    return bool(value)
