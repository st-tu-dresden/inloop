from unittest import TestCase

from django.conf import settings

from markdown import Markdown

from inloop.common.templatetags.markdown import GitVersionProvider, ImageVersionExtension


class GitVersionProviderTest(TestCase):
    def test_get_version(self):
        version = GitVersionProvider(settings.BASE_DIR).get_version()
        self.assertRegex(version, r'^[0-9a-z]{4,}$')


class DummyVersionProvider:
    def get_version(self):
        return 'cafebabe'


class NoneVersionProvider:
    def get_version(self):
        return None


class ImageVersioningTest(TestCase):
    def setUp(self):
        self.md = Markdown(output_format='html5', extensions=[
            ImageVersionExtension(DummyVersionProvider())
        ])

    def test_version_is_appended(self):
        html = self.md.convert('![alt text](https://example.com/a/b/c.jpeg)')
        self.assertIn('src="https://example.com/a/b/c.jpeg?v=cafebabe"', html)

    def test_code_block_is_ignored(self):
        html = self.md.convert(
            """
            ```html
            <img src="example.com/1.psd">
            ```
            """
        )
        self.assertNotIn('v=cafebabe', html)

    def test_ordinary_link_is_ignored(self):
        html = self.md.convert('[foo bar baz](path/to/image.png)')
        self.assertIn('href="path/to/image.png"', html)

    def test_empty_src_tag_is_ignored(self):
        html = self.md.convert('![alt]()')
        self.assertNotIn('v=cafebabe', html)


class NoopImageVersioningTest(TestCase):
    def setUp(self):
        self.md = Markdown(output_format='html5', extensions=[
            ImageVersionExtension(NoneVersionProvider())
        ])

    def test_no_version_is_appended(self):
        html = self.md.convert('![alt text](https://example.com/a/b/c.jpeg)')
        self.assertIn('src="https://example.com/a/b/c.jpeg"', html)
