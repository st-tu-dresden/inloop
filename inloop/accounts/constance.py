import re
from collections import OrderedDict

from django.utils.text import mark_safe

from inloop.common.validators import RegexSyntaxValidator

config = OrderedDict()
config['SIGNUP_ALLOWED'] = (False, mark_safe('Allow or disallow new users to sign up.'))
config['EMAIL_PATTERN'] = ('', mark_safe(
    'A Python regular expression used to test email addresses during sign up. The '
    'regex is compiled using <code>re.VERBOSE</code>, which means you can use '
    'comments and whitespace (which will be ignored) to structure the regex.'), 'regex'
)
config['EMAIL_HELP_TEXT'] = ('', mark_safe(
    'Form field help text with a human-friendly description of <code>EMAIL_PATTERN</code>.'
))
config['EMAIL_ERROR_MESSAGE'] = ('', mark_safe(
    "Form field error message in case <code>EMAIL_PATTERN</code> doesn't match."
))

fieldsets = {
    'Signup form settings': ['SIGNUP_ALLOWED', 'EMAIL_PATTERN',
                             'EMAIL_HELP_TEXT', 'EMAIL_ERROR_MESSAGE']
}

fields = {
    'regex': ['django.forms.CharField', {
        'widget': 'django.forms.Textarea',
        'validators': [RegexSyntaxValidator(re.VERBOSE)],
        'required': False
    }],
}
