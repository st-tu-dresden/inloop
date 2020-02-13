import subprocess

from django.conf import settings
from django.template import Library
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

from markdown import Extension, Markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.treeprocessors import Treeprocessor


class ImageVersionTreeprocessor(Treeprocessor):
    """Markdown tree processor that appends version strings to image resources."""

    def __init__(self, version_provider, *args, **kwargs):
        self.version_provider = version_provider
        super().__init__(*args, **kwargs)

    def run(self, root):
        """
        Traverse the tree and add the version id to the src attribute
        of all <img> tags to control browser image caching based on the
        given version id.
        """
        version_id = self.version_provider.get_version()
        if version_id is None:
            return
        img_nodes = root.iter('img')
        for node in img_nodes:
            url = node.get('src')
            if not url:
                continue
            if url.startswith('https://') or url.startswith('http://'):
                # note that the comparison is intentionally case-sensitive
                continue
            node.set('src', f'{url}?v={version_id}')


class ImageVersionExtension(Extension):
    """Markdown extension that appends version strings to image resources."""

    def __init__(self, version_provider, *args, **kwargs):
        """Create an image version extension."""
        self.version_provider = version_provider
        super().__init__(*args, **kwargs)

    def extendMarkdown(self, md, md_globals):
        """Wrap the custom image version treeprocessor."""
        md.treeprocessors.add(
            'image_version_extension',
            ImageVersionTreeprocessor(self.version_provider, md),
            '_end'
        )


class GitVersionProvider:
    """Provides a version string based on the id of a repo's latest commit."""

    args = 'git rev-parse --short HEAD'.split()

    def __init__(self, repo):
        """Initialize with the given path to a Git repository."""
        self.repo = repo

    def get_version(self):
        """Return the short id of the latest commit or None if it can't be determined."""
        try:
            result = subprocess.run(
                self.args,
                cwd=self.repo,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                universal_newlines=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except OSError:
            pass


register = Library()
convert = Markdown(output_format='html5', extensions=[
    'markdown.extensions.toc',
    'markdown.extensions.smarty',
    'markdown.extensions.fenced_code',
    'markdown.extensions.tables',
    CodeHiliteExtension(use_pygments=False),
    ImageVersionExtension(GitVersionProvider(settings.REPOSITORY_ROOT)),
]).convert


@register.filter(is_safe=True)
@stringfilter
def markdown(value):
    return mark_safe(convert(value))
