import re

from django.core.exceptions import ValidationError


def validate_password(value):
    if len(str(value)) < 8:
        raise ValidationError('The password must have at least 8 characters!')
    if not any(c.isdigit() for c in value):
        raise ValidationError('The password must contain at least one number!')


def validate_mat_num(value):
    if len(str(value)) != 7:
        raise ValidationError('The matriculation number consists of 7 digits.')


def validate_zih_mail(value):
    patterns = [
        '^s[0-9]{7}@mail.zih.tu-dresden.de$',
        '^[^@]+@mailbox.tu-dresden.de$',
        '^[^@]+@tu-dresden.de$',
    ]
    for pattern in patterns:
        if re.search(pattern, value):
            return

    raise ValidationError("We only accept valid TU Dresden email addresses.")
