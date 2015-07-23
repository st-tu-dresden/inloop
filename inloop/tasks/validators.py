from django.core.exceptions import ValidationError
import re


def validate_short_id(value):
    reg = re.compile('([A-Za-z][A-Za-z1-9])')
    if len(str(value)) != 2:
        raise ValidationError('The short id is too long!')
    elif not reg.match(str(value)):
        raise ValidationError('The short id must not contain'
                              'special characters or start'
                              ' with a number!')
