import re
from typing import Optional

from django.core.exceptions import ValidationError

DATE_INPUTFORMAT_REGEX = re.compile(r"""
    [0-9]{4}-[0-9]{2}-[0-9]{2}$ # The day, such as 1970-01-01
""", re.VERBOSE)

ISOFORMAT_REGEX = re.compile(r"""
    [0-9]{4}-[0-9]{2}-[0-9]{2}               # The day, such as 1970-01-01
    T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}Z$  # The time, such as 00:00:00.000Z
""", re.VERBOSE)


def get_optional_timestamp(key_name: str, data: dict) -> Optional[str]:
    """
    Get and validate an optional timestamp from a data dictionary.

    Timestamps must conform to the iso format implementation
    of JavaScript to be directly parseable by the database backend.
    """
    parameter = data.get(key_name)
    if not parameter:
        return None
    # Try to match supported date formats
    # from the most to the least specific
    match = ISOFORMAT_REGEX.match(parameter)
    if match is not None:
        return parameter
    match = DATE_INPUTFORMAT_REGEX.match(parameter)
    if match is not None:
        return parameter
    raise ValidationError(
        f'Timestamp parameter "{key_name}" was supplied '
        f'with the value {parameter!r} but is not in valid iso format.'
    )


def get_optional_bool(key_name: str, data: dict) -> Optional[bool]:
    """
    Get and validate a boolean parameter from a data dictionary.
    """
    parameter = data.get(key_name)
    if parameter is None or parameter == "":
        return None
    if isinstance(parameter, bool):
        return parameter
    if isinstance(parameter, int):
        return bool(parameter)
    if isinstance(parameter, str):
        if parameter.lower() == "true":
            return True
        if parameter.lower() == "false":
            return False
    raise ValidationError(
        f'Boolean parameter "{key_name}" was supplied '
        f'with the value {parameter!r} but is not a boolean value.'
    )


def get_optional_int(key_name: str, data: dict) -> Optional[int]:
    """
    Get and validate an integer parameter from a data dictionary.
    """
    parameter = data.get(key_name)
    if parameter is None or parameter == "":
        return None
    if isinstance(parameter, int):
        return parameter
    if isinstance(parameter, str):
        try:
            return int(parameter)
        except ValueError:
            pass
    raise ValidationError(
        f'Integer parameter "{key_name}" was supplied '
        f'with the value {parameter!r} but is not an integer value.'
    )


ALLOWED_TRUNCATOR_IDENTIFIERS = ['minute', 'hour', 'day', 'month', 'year']


def get_optional_truncator_identifier(key_name: str, data: dict) -> Optional[str]:
    """
    Get and validate an SQL truncator identifier from a data dictionary.
    """
    truncator_identifier = data.get(key_name)
    if not truncator_identifier:
        return None
    if truncator_identifier in ALLOWED_TRUNCATOR_IDENTIFIERS:
        return truncator_identifier
    raise ValidationError(
        f'Truncator identifier parameter "{key_name}" was supplied '
        f'with the value {truncator_identifier!r} but is not allowed. '
        f'Allowed truncator identifiers are {ALLOWED_TRUNCATOR_IDENTIFIERS}'
    )
