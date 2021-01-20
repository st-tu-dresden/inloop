import re
from re import RegexFlag
from typing import Union

from django.core.exceptions import ValidationError


class RegexSyntaxValidator:
    """Validate whether a given regex compiles without errors."""

    def __init__(self, flags: Union[int, RegexFlag] = 0) -> None:
        self.flags = flags

    def __call__(self, regex: str) -> None:
        try:
            re.compile(regex, self.flags)
        except re.error as error:
            raise ValidationError(f"Invalid regex: {error}")
