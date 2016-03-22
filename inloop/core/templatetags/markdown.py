from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from markdown import Markdown

register = template.Library()
_markdown = Markdown(
    output_format='html5',
    extensions=[
        "markdown.extensions.toc",
        "markdown.extensions.smarty",
        "markdown.extensions.fenced_code",
        "markdown.extensions.codehilite"
    ]
)


@register.filter(is_safe=True)
@stringfilter
def markdown(value):
    return mark_safe(_markdown.convert(value))
