from __future__ import annotations

import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional, Union
from xml.etree.ElementTree import Element

from django.conf import settings
from django.template import Library
from django.template.defaultfilters import stringfilter
from django.utils.safestring import SafeText, mark_safe

from markdown import Markdown
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor


class VersionProvider(ABC):
    @abstractmethod
    def get_version(self) -> Optional[str]:
        pass


class ImageVersionTreeprocessor(Treeprocessor):
    """Markdown tree processor that appends version strings to image resources."""

    def __init__(self, version_provider: VersionProvider, *args: Any, **kwargs: Any) -> None:
        self.version_provider = version_provider
        super().__init__(*args, **kwargs)

    def run(self, root: Element) -> None:
        """
        Traverse the tree and add the version id to the src attribute
        of all <img> tags to control browser image caching based on the
        given version id.
        """
        version_id = self.version_provider.get_version()
        if version_id is None:
            return
        img_nodes = root.iter("img")
        for node in img_nodes:
            url = node.get("src")
            if not url:
                continue
            if url.startswith("https://") or url.startswith("http://"):
                # note that the comparison is intentionally case-sensitive
                continue
            node.set("src", f"{url}?v={version_id}")


class ImageVersionExtension(Extension):
    """Markdown extension that appends version strings to image resources."""

    def __init__(self, version_provider: VersionProvider, *args: Any, **kwargs: Any) -> None:
        """Create an image version extension."""
        self.version_provider = version_provider
        super().__init__(*args, **kwargs)

    def extendMarkdown(self, md: Markdown) -> None:
        """Wrap the custom image version treeprocessor."""
        processor = ImageVersionTreeprocessor(self.version_provider, md)
        md.treeprocessors.register(  # pytype: disable=attribute-error
            processor, "image_version_extension", 0
        )


class GitVersionProvider(VersionProvider):
    """Provides a version string based on the id of a repo's latest commit."""

    args = "git rev-parse --short HEAD".split()

    def __init__(self, repo: Optional[Union[str, Path]]) -> None:
        """Initialize with the given path to a Git repository."""
        self.repo = repo

    def get_version(self) -> Optional[str]:
        """Return the short id of the latest commit or None if it can't be determined."""
        try:
            result = subprocess.run(
                self.args,
                cwd=self.repo,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                universal_newlines=True,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except OSError:
            pass


register = Library()
convert = Markdown(
    output_format="html",
    extensions=[
        "markdown.extensions.toc",
        "markdown.extensions.smarty",
        "markdown.extensions.fenced_code",
        "markdown.extensions.tables",
        ImageVersionExtension(GitVersionProvider(settings.REPOSITORY_ROOT)),
    ],
).convert


@register.filter(is_safe=True)
@stringfilter
def markdown(value: str) -> SafeText:
    return mark_safe(convert(value))
