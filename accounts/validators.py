from django.core.exceptions import ValidationError

def validate_mat_num(value):
    if len(str(value)) != 7:
        print "Validation of mat_num failed!"
        raise ValidationError("The matriculation number does not have 7 digits!")