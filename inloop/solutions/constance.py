from django.utils.safestring import mark_safe

config = {
    'ALLOWED_FILENAME_EXTENSIONS': ('.java', mark_safe(
        'Filename extensions to be accepted in solution upload forms '
        'such as <code>.java, .c, .cpp, .h, .hpp</code>. '
        'Separate multiple filename extensions by commas. '
        'Surrounding whitespace will be stripped and '
        'filename extensions will be treated case insensitive.'
    )),
    'SYNTAX_CHECK_ENDPOINT': ('', (
        'The URL of the syntax check endpoint. If empty, syntax checks '
        'will be disabled globally.'
    )),
}

fieldsets = {
    'General settings': ['ALLOWED_FILENAME_EXTENSIONS'],
    'Syntax check': ['SYNTAX_CHECK_ENDPOINT']
}
