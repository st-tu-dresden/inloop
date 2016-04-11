from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

from markdown import Markdown
from markdown.extensions.codehilite import CodeHiliteExtension

register = template.Library()
_markdown = Markdown(
    output_format='html5',
    extensions=[
        "markdown.extensions.toc",
        "markdown.extensions.smarty",
        "markdown.extensions.fenced_code",
        CodeHiliteExtension(use_pygments=False)
    ]
)


@register.filter(is_safe=True)
@stringfilter
def markdown(value):
    return mark_safe(_markdown.convert(value))
