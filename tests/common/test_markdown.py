from django.test import TestCase

from markdown import Markdown

from inloop.common.templatetags.markdown import (GitImageVersionExtension, ImageVersionExtension,
                                                 ImageVersionTreeprocessor)


class ImageVersionTreeprocessorTestCase(TestCase):
    def test_conflicting_image_version(self):
        """
        Verify, that version ids must be
        alphanumerical to avoid html conflicts.
        """
        try:
            _ = ImageVersionTreeprocessor("/test/")
            self.fail("Should fail with a ValueError.")
        except ValueError:
            pass


class ImageVersionExtensionTestCase(TestCase):
    """Test the image version markdown extension."""

    def setUp(self) -> None:
        self.version_id = "1337"
        self.md = Markdown(output_format="html5", extensions=[
            ImageVersionExtension(self.version_id),
        ])

    def test_image_versioning(self):
        """Verify, that inline styled images are supplied with a hash."""
        html = self.md.convert('![alt text](https://example.com/a/b/c.jpeg) "Title"')
        self.assertIn('src="https://example.com/a/b/c.jpeg?version_id=1337"', html)

    def test_ignore_html_code(self):
        """
        Validate, that html in code blocks is
        ignored by the image version extension.
        """
        html = self.md.convert(
            """
            ```python
            test = <img src="example.com/1.psd">
            ```
            """
        )
        self.assertNotIn("version_id", html)
        self.assertNotIn("1337", html)

    def test_ignore_empty_src_tags(self):
        """
        Validate, that img nodes without
        a specified source are not processed.
        """
        html = self.md.convert('![alt]()')
        self.assertIn("img", html)
        self.assertNotIn("version_id", html)
        self.assertNotIn("1337", html)


class ConflictingImageVersionTestCase(TestCase):
    def test_conflicting_image_version(self):
        """
        Verify, that version ids must be
        alphanumerical to avoid html conflicts.
        """
        try:
            _ = Markdown(output_format="html5", extensions=[
                ImageVersionExtension("/test/"),
            ])
            self.fail("Should fail with a ValueError.")
        except ValueError:
            pass


class GitImageVersionTestCase(TestCase):
    def test_git_version_id(self):
        """Validate, that the current git commit hash is extracted correctly."""
        e = GitImageVersionExtension()
        self.assertEqual(len(e.version_id), 40)
        self.assertTrue(e.version_id.isalnum())
        self.assertEqual(len(e.version_id), len(e.version_id.strip()))
