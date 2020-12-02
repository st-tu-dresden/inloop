from unittest import TestCase

from inloop.common.templatetags.markdown import markdown

FENCED_CODE = """
```python
print("Hello, World")
```
"""

MARKDOWN_TABLE = """
|A|B|
|---|---|
|Test 1|Test 2|
"""


class TestMarkdownFilter(TestCase):
    def test_autoids(self):
        html = markdown("# Heading")
        self.assertTrue('<h1 id="heading">Heading</h1>' in html)

    def test_fenced_code(self):
        html = markdown(FENCED_CODE)
        self.assertTrue('<code class="language-python">' in html)

    def test_markdown_tables(self):
        html = markdown(MARKDOWN_TABLE)
        signature_expressions = [
            "<table>",
            "<thead>",
            "<tr>",
            "<th>A</th>",
            "<tbody>",
            "<td>Test 1</td>",
        ]
        for expression in signature_expressions:
            self.assertTrue(expression in html)
