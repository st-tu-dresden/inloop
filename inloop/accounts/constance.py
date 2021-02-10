import re
from collections import OrderedDict

from django.utils.safestring import mark_safe

from inloop.common.validators import RegexSyntaxValidator

config = OrderedDict()
config["SIGNUP_ALLOWED"] = (False, mark_safe("Allow or disallow new users to sign up."))
config["EMAIL_PATTERN"] = (
    "",
    mark_safe(
        "A Python regular expression used to test email addresses during sign up. The "
        "regex is compiled using <code>re.VERBOSE</code>, which means you can use "
        "comments and whitespace (which will be ignored) to structure the regex."
    ),
    "regex",
)
config["EMAIL_HELP_TEXT"] = (
    "",
    mark_safe(
        "Form field help text with a human-friendly description of <code>EMAIL_PATTERN</code>."
    ),
)
config["EMAIL_ERROR_MESSAGE"] = (
    "",
    mark_safe("Form field error message in case <code>EMAIL_PATTERN</code> doesn't match."),
)
config["REQUIRE_OWNWORK_DECLARATION"] = (
    False,
    mark_safe("If checked, users need to confirm the own work declaration to proceed."),
)
config["OWNWORK_DECLARATION_INTRO"] = (
    "",
    mark_safe(
        "Text that will be displayed above the own work confirmation form " "(supports Markdown)."
    ),
)
config["OWNWORK_DECLARATION"] = (
    "",
    mark_safe(
        "Text that will be displayed next to the own work confirmation checkbox "
        "(supports Markdown)."
    ),
)
config["AUTO_ASSIGN_GROUPS"] = (
    "",
    mark_safe(
        "If not empty, users which have not yet a group will be assigned to one of "
        "the listed groups randomly on login. Group names are separated by spaces."
    ),
)

fieldsets = {
    "Signup form settings": [
        "SIGNUP_ALLOWED",
        "EMAIL_PATTERN",
        "EMAIL_HELP_TEXT",
        "EMAIL_ERROR_MESSAGE",
    ],
    "Own work declaration": [
        "REQUIRE_OWNWORK_DECLARATION",
        "OWNWORK_DECLARATION_INTRO",
        "OWNWORK_DECLARATION",
    ],
    "Group assignments": ["AUTO_ASSIGN_GROUPS"],
}

fields = {
    "regex": [
        "django.forms.CharField",
        {
            "widget": "django.forms.Textarea",
            "validators": [RegexSyntaxValidator(re.VERBOSE)],
            "required": False,
        },
    ],
}
