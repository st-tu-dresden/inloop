"""Markdown Package.

To provide dynamic Markdown rendering, we use the Markdown package.

.. _Markdown package:
   https://pypi.python.org/pypi/Markdown

.. _Markdown package extensions
   https://python-markdown.github.io/extensions/
"""
import subprocess

from django.conf import settings
from django.template import Library
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

from markdown import Extension, Markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.treeprocessors import Treeprocessor


class ImageVersionTreeprocessor(Treeprocessor):
    """Provide a tree processor for image versioning."""

    def __init__(self, version_id: str, *args, **kwargs):
        """Create an image version tree processor."""
        if not version_id.isalnum():
            raise ValueError(
                "The supplied version id should be alphanumerical "
                "to avoid unwanted html conflicts. Given id: {}"
                .format(version_id)
            )
        self.version_id = version_id
        super().__init__(*args, **kwargs)

    def run(self, root):
        """
        Process the document root node.

        Add the version id to the src attribute of all img tags to
        control browser image caching based on the given version id.
        """
        img_nodes = root.findall("*/img")
        for node in img_nodes:
            old_src = node.get("src")
            if not old_src:
                continue
            new_src = "{}?version_id={}".format(old_src, self.version_id)
            node.set("src", new_src)
        return root


class ImageVersionExtension(Extension):
    """Represent a custom extension for the markdown package."""

    def __init__(self, version_id: str, *args, **kwargs):
        """Create an image version extension."""
        if not version_id.isalnum():
            raise ValueError(
                "The supplied version id should be alphanumerical "
                "to avoid unwanted html conflicts. Given id: {}"
                .format(version_id)
            )
        self.version_id = version_id
        super().__init__(*args, **kwargs)

    def extendMarkdown(self, md, md_globals):
        """Wrap the custom image version treeprocessor."""
        md.treeprocessors.add(
            "image_version_extension",
            ImageVersionTreeprocessor(self.version_id, md),
            "_end"
        )


class GitImageVersionExtension(ImageVersionExtension):
    """
    Provide a git hash based convenience wrapper
    for the image version extension.
    """

    def __init__(self, *args, **kwargs):
        """Create a git image version extension."""
        version_id = subprocess.check_output([
            "git",
            "-C",
            str(settings.BASE_DIR),
            "rev-parse",
            "HEAD",
        ]).decode().strip()
        super().__init__(version_id=version_id, *args, **kwargs)


register = Library()
convert = Markdown(output_format='html5', extensions=[
    'markdown.extensions.toc',
    'markdown.extensions.smarty',
    'markdown.extensions.fenced_code',
    'markdown.extensions.tables',
    CodeHiliteExtension(use_pygments=False),
    GitImageVersionExtension(),
]).convert


@register.filter(is_safe=True)
@stringfilter
def markdown(value):
    return mark_safe(convert(value))
