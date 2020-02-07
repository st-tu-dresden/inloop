from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from django.conf import settings

from markdown import Markdown

from inloop.common.templatetags.markdown import GitVersionProvider, ImageVersionExtension


class GitVersionProviderTest(TestCase):
    def test_none_is_returned_for_non_git_dir(self):
        with TemporaryDirectory() as tmpdir:
            version = GitVersionProvider(tmpdir).get_version()
            self.assertIsNone(version)

    def test_none_is_returned_for_nonexistent_dir(self):
        with TemporaryDirectory() as tmpdir:
            version = GitVersionProvider(Path(tmpdir, 'does_not_exist')).get_version()
            self.assertIsNone(version)

    def test_get_version(self):
        version = GitVersionProvider(settings.BASE_DIR).get_version()
        self.assertRegex(version, r'^[0-9a-z]{4,}$')


class DummyVersionProvider:
    def get_version(self):
        return 'cafebabe'


class ImageVersioningTest(TestCase):
    def setUp(self):
        self.md = Markdown(output_format='html5', extensions=[
            ImageVersionExtension(DummyVersionProvider())
        ])

    def test_version_is_appended1(self):
        html = self.md.convert('![alt text](/a/b/c.jpeg)')
        self.assertIn('src="/a/b/c.jpeg?v=cafebabe"', html)

    def test_version_is_appended2(self):
        html = self.md.convert('![alt text](a/b/c.jpeg)')
        self.assertIn('src="a/b/c.jpeg?v=cafebabe"', html)

    def test_version_is_appended_in_nested_img_tags(self):
        html = self.md.convert('* ![alt text](a/b/c.jpeg)')
        self.assertTrue(html.startswith('<ul>'))
        self.assertTrue(html.endswith('</ul>'))
        self.assertIn('src="a/b/c.jpeg?v=cafebabe"', html)

    def test_absolute_http_url_is_ignored(self):
        html = self.md.convert('![alt text](http://example.com/a/b/c.jpeg)')
        self.assertIn('src="http://example.com/a/b/c.jpeg"', html)

    def test_absolute_https_url_is_ignored(self):
        html = self.md.convert('![alt text](https://example.com/a/b/c.jpeg)')
        self.assertIn('src="https://example.com/a/b/c.jpeg"', html)

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


class NoneVersionProvider:
    def get_version(self):
        return None


class NoopImageVersioningTest(TestCase):
    def setUp(self):
        self.md = Markdown(output_format='html5', extensions=[
            ImageVersionExtension(NoneVersionProvider())
        ])

    def test_no_version_is_appended(self):
        html = self.md.convert('![alt text](a/b/c.jpeg)')
        self.assertIn('src="a/b/c.jpeg"', html)
