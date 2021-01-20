from django import forms
from django.core.exceptions import ValidationError

ALLOWED_TRUNCATOR_IDENTIFIERS = ["minute", "hour", "day", "month", "year"]
VALID_DATETIME_FORMATS = ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%d"]


def validate_granularity(value: str) -> None:
    """
    Validate that a given value corresponds to
    a supported SQL truncator identifier.
    """
    if value not in ALLOWED_TRUNCATOR_IDENTIFIERS:
        raise ValidationError(
            f"Granularity was supplied with the value {value} but is not allowed. "
            f"Allowed granularities are {ALLOWED_TRUNCATOR_IDENTIFIERS}."
        )


class SubmissionsHistogramForm(forms.Form):
    queryset_limit = forms.IntegerField(required=False)
    from_timestamp = forms.DateTimeField(input_formats=VALID_DATETIME_FORMATS, required=False)
    to_timestamp = forms.DateTimeField(input_formats=VALID_DATETIME_FORMATS, required=False)
    passed = forms.NullBooleanField(required=False)
    category_id = forms.IntegerField(required=False)
    granularity = forms.CharField(validators=[validate_granularity], required=False)


class AttemptsHistogramForm(forms.Form):
    queryset_limit = forms.IntegerField(required=False)
    task_id = forms.IntegerField()
