from unittest import TestCase

from defusedxml import ElementTree

from inloop.solutions.prettyprint.checkstyle import (context_from_xml_strings,
                                                     element_tree_to_dict, extract_items_by_key)

from . import SAMPLES_PATH

with SAMPLES_PATH.joinpath("checkstyle.xml").open() as fp:
    CHECKSTYLE_SAMPLE_XML = fp.read()

CHECKSTYLE_SAMPLE_DATA = [{
    'version': '8.9'
}, {
    'tag':
    'checkstyle',
    'attrib': {
        'version': '8.9'
    },
    'text':
    '\n',
    'children': [{
        'tag':
        'file',
        'attrib': {
            'name': '/checker/input/Book.java'
        },
        'text':
        '\n',
        'children': [{
            'tag': 'error',
            'attrib': {
                'line': '0',
                'severity': 'error',
                'message': 'File does not end with a newline.',
                'source': 'checks.NewlineAtEndOfFileCheck'
            },
            'text': None,
            'children': []
        }, {
            'tag': 'error',
            'attrib': {
                'line': '1',
                'column': '9',
                'severity': 'warning',
                'message': "Name 'U01.src' must match pattern"
                " '^[a-z]+(\\.[a-z][a-z0-9]{1,})*$'.",
                'source': 'checks.naming.PackageNameCheck'
            },
            'text': None,
            'children': []
        }, {
            'tag': 'error',
            'attrib': {
                'line': '1',
                'column': '17',
                'severity': 'error',
                'message': "';' is not followed by whitespace.",
                'source': 'checks.whitespace.WhitespaceAfterCheck'
            },
            'text': None,
            'children': []
        }]
    }]
}]


class CheckstyleXMLTests(TestCase):
    def setUp(self):
        super().setUp()
        self.xml_strings_context = context_from_xml_strings(
            xml_strings=[CHECKSTYLE_SAMPLE_XML], filter_keys=[])

    def test_extract(self):
        data = extract_items_by_key(data=CHECKSTYLE_SAMPLE_DATA, key="file")
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["tag"], "file")
        self.assertEqual(len(data[0]["children"]), 3)

    def test_to_dict(self):
        element_tree = ElementTree.fromstring(CHECKSTYLE_SAMPLE_XML)
        dictionary1 = element_tree_to_dict(element_tree, filter_keys=[])
        dictionary2 = element_tree_to_dict(element_tree, filter_keys=None)
        for dictionary in [dictionary1, dictionary2]:
            self.assertTrue(isinstance(dictionary, dict))
            self.assertEqual(dictionary["tag"], "checkstyle")
            self.assertTrue(len(dictionary["children"]) > 0)
            self.assertEqual(dictionary["attrib"]["version"], "8.9")

    def test_extract_none(self):
        data1 = extract_items_by_key(data=None, key=None)
        data2 = extract_items_by_key(data=CHECKSTYLE_SAMPLE_DATA, key=None)
        data3 = extract_items_by_key(data=None, key="file")
        for data in [data1, data2, data3]:
            self.assertEqual(data, [])

    def test_etree_empty_args(self):
        with self.assertRaises(AttributeError):
            element_tree_to_dict(None, filter_keys=[])

    def test_xml_parsing(self):
        contents = str(self.xml_strings_context)
        self.assertTrue("'if' is not preceded with whitespace." in contents)
        self.assertTrue("'{' at column 52 should have line break after." in contents)
        self.assertTrue("';' is not followed by whitespace." in contents)
