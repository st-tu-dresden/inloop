"""Markdown Package.

To provide dynamic Markdown rendering, we use the Markdown package.

.. _Markdown package:
   https://pypi.python.org/pypi/Markdown

.. _Markdown package extensions
   https://python-markdown.github.io/extensions/
"""

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
    "markdown.extensions.tables",
    CodeHiliteExtension(use_pygments=False)
]).convert


@register.filter(is_safe=True)
@stringfilter
def markdown(value):
    return mark_safe(convert(value))
