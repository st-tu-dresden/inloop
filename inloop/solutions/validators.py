from django.core.exceptions import ValidationError

from constance import config


def _get_allowed_filename_extensions():
    """
    Return all allowed filename extensions.
    """
    allowed_filename_extensions = config.ALLOWED_FILENAME_EXTENSIONS
    if not allowed_filename_extensions:
        return None
    return [e.strip().lower() for e in allowed_filename_extensions.split(",")]


def validate_filenames(upload):
    """
    Verify that all uploaded files comply to the given naming constraints.
    """
    allowed_filename_extensions = _get_allowed_filename_extensions()
    if not allowed_filename_extensions:
        raise ValidationError("Currently no filename extensions are accepted.")
    if not upload:
        raise ValidationError("No files were supplied.")
    for file_name, _ in upload.items():
        if not file_name.lower().endswith(tuple(allowed_filename_extensions)):
            raise ValidationError(
                "One or more files contain disallowed filename extensions. "
                "(Allowed: {})".format(", ".join(allowed_filename_extensions))
            )
