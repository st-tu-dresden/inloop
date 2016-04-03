from unittest import skipIf

from django.test import TestCase

from inloop.core.templatetags.markdown import markdown

try:
    import pygments
except ImportError:
    pygments = None


FENCED_CODE = """
```python
print("Hello, World")
```
"""


class TestMarkdownFilter(TestCase):
    def test_autoids(self):
        html = markdown('# Heading')
        self.assertIn('<h1 id="heading">Heading</h1>', html)

    # TODO
    @skipIf(pygments, "This fails if pygments is installed.")
    def test_fenced_code(self):
        html = markdown(FENCED_CODE)
        self.assertIn('<code class="language-python">', html)
