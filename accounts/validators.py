from django.core.exceptions import ValidationError


def validate_password(value):
    if len(str(value)) < 8:
        raise ValidationError('The password must have at least 8 characters!')
    if not any(c.isdigit() for c in value):
        raise ValidationError('The password must contain at least one number!')


def validate_mat_num(value):
    if len(str(value)) != 7:
        raise ValidationError('The matriculation number'
                              ' does not have 7 digits!')
