from collections import OrderedDict

from django.utils.safestring import mark_safe

config = OrderedDict()
config["ALLOWED_FILENAME_EXTENSIONS"] = (".java", mark_safe(
    "Filename extensions to be accepted in solution upload forms "
    "such as <code>.java, .c, .cpp, .h, .hpp</code>. "
    "Separate multiple filename extensions by commas."
    "Surrounding whitespace will be stripped."
))

fieldsets = {"General settings": ["ALLOWED_FILENAME_EXTENSIONS"]}
