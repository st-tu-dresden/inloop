import re

from django.core.exceptions import ValidationError


class RegexSyntaxValidator:
    """Validate whether a given regex compiles without errors."""

    def __init__(self, flags=0):
        self.flags = flags

    def __call__(self, regex):
        try:
            re.compile(regex, self.flags)
        except re.error as error:
            raise ValidationError(f'Invalid regex: {error}')
