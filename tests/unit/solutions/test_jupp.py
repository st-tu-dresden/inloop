from pathlib import Path
from unittest import TestCase

from inloop.solutions.prettyprint import tools

SAMPLES_PATH = Path(__file__).parent.joinpath("samples")
with SAMPLES_PATH.joinpath("TEST-TaxiTest.xml").open() as fp:
    SAMPLE_XML_JUNIT = fp.read()
with SAMPLES_PATH.joinpath("Checkstyle.xml").open() as fp:
    SAMPLE_XML_CHECKSTYLE = fp.read()
with SAMPLES_PATH.joinpath("billion_laughs.xml").open() as fp:
    MALICIOUS_XML = fp.read()

SAMPLE_DICT = [
    {'version': '8.9'},
    {
        'tag': 'checkstyle',
        'attrib': {'version': '8.9'},
        'text': '\n',
        'children': [
            {
                'tag': 'file',
                'attrib': {'name': '/checker/input/Book.java'},
                'text': '\n',
                'children': [
                    {
                        'tag': 'error',
                        'attrib': {
                            'line': '0',
                            'severity': 'error',
                            'message': 'File does not end with a newline.',
                            'source': 'checks.NewlineAtEndOfFileCheck'
                        },
                        'text': None,
                        'children': []
                    },
                    {
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
                    },
                    {
                        'tag': 'error',
                        'attrib': {
                            'line': '1',
                            'column': '17',
                            'severity': 'error',
                            'message': "';' is not followed by whitespace.",
                            'source': 'checks.whitespace.WhitespaceAfterCheck'},
                        'text': None,
                        'children': []
                    }
                ]
            }
        ]
    }
]


class JUnitXMLTests(TestCase):
    def setUp(self):
        self.ts = tools.xml_to_dict(SAMPLE_XML_JUNIT)

    def test_sample_outputs(self):
        self.assertTrue(self.ts["system_out"].startswith("Andrea Bora"))
        self.assertEqual(self.ts["system_err"], None)

    def test_sample_attributes(self):
        self.assertEqual(self.ts["total"], 5)
        self.assertEqual(self.ts["errors"], 0)
        self.assertEqual(self.ts["failures"], 1)
        self.assertEqual(self.ts["passed"], 4)
        self.assertEqual(self.ts["name"], "TaxiTest")

    def test_sample_testcases(self):
        testcases = self.ts["testcases"]
        self.assertEqual(len(testcases), 5)

        tc1 = testcases[0]
        self.assertEqual(tc1["name"], "testTaxiAdd")
        self.assertFalse(hasattr(tc1, "failure"))

        tc2 = testcases[4]
        self.assertEqual(tc2["name"], "taxiAllGetOutTaxiNotEmpty")
        failure = tc2["failure"]
        self.assertEqual(failure["type"], "junit.framework.AssertionFailedError")
        self.assertIn("allGetOut()", failure["message"])
        self.assertIn("allGetOut()", failure["stacktrace"])

        tc3 = testcases[3]
        self.assertEqual(tc3["name"], "testTaxiDriverAssigned")
        error = tc3["error"]
        self.assertEqual(error["type"], "java.lang.IllegalArgumentException")
        self.assertEqual("Sample message", error["message"])
        self.assertIn("Exception: Sample message", error["stacktrace"])

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            tools.xml_to_dict("<invalid-root />")

    def test_no_testcases(self):
        ts = tools.xml_to_dict("<testsuite><system-out /><system-err /></testsuite>")
        self.assertEqual(len(ts["testcases"]), 0)

    def test_missing_systemerr_or_systemout(self):
        documents = [
            "<testsuite><system-err /></testsuite>",
            "<testsuite><system-out /></testsuite>",
            "<testsuite></testsuite>",
        ]
        for document in documents:
            ts = tools.xml_to_dict(document)
            self.assertEqual(len(ts["testcases"]), 0)


class XMLBombProtectionTest(TestCase):
    def test_malicious_xmlfile(self):
        with self.assertRaises(ValueError):
            tools.xml_to_dict(MALICIOUS_XML)


class CheckstyleXMLTests(TestCase):
    pass
