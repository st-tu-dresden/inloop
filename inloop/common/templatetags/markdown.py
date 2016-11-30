from django.template import Library
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

from markdown import Markdown
from markdown.extensions.codehilite import CodeHiliteExtension

register = Library()
convert = Markdown(output_format="html5", extensions=[
    "markdown.extensions.toc",
    "markdown.extensions.smarty",
    "markdown.extensions.fenced_code",
    CodeHiliteExtension(use_pygments=False)
]).convert


@register.filter(is_safe=True)
@stringfilter
def markdown(value):
    return mark_safe(convert(value))
