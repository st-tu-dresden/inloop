from unittest import TestCase

from inloop.common.templatetags.markdown import markdown

FENCED_CODE = """
```python
print("Hello, World")
```
"""


class TestMarkdownFilter(TestCase):
    def test_autoids(self):
        html = markdown('# Heading')
        self.assertTrue('<h1 id="heading">Heading</h1>' in html)

    def test_fenced_code(self):
        html = markdown(FENCED_CODE)
        self.assertTrue('<code class="language-python">' in html)
