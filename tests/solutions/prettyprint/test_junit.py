from pathlib import Path
from unittest import TestCase

from inloop.solutions.prettyprint import junit

from . import SAMPLES_PATH

with open(SAMPLES_PATH / 'TEST-TaxiTest.xml') as stream:
    JUNIT_SAMPLE_XML = stream.read()
with open(SAMPLES_PATH / 'billion_laughs.xml') as stream:
    MALICIOUS_XML = stream.read()


class JUnitXMLTests(TestCase):
    def setUp(self):
        self.ts = junit.xml_to_dict(JUNIT_SAMPLE_XML)

    def test_sample_outputs(self):
        self.assertTrue(self.ts['system_out'].startswith('Andrea Bora'))
        self.assertEqual(self.ts['system_err'], None)

    def test_sample_attributes(self):
        self.assertEqual(self.ts['total'], 5)
        self.assertEqual(self.ts['errors'], 0)
        self.assertEqual(self.ts['failures'], 1)
        self.assertEqual(self.ts['passed'], 4)
        self.assertEqual(self.ts['name'], 'TaxiTest')

    def test_sample_testcases(self):
        testcases = self.ts['testcases']
        self.assertEqual(len(testcases), 5)

        tc1 = testcases[0]
        self.assertEqual(tc1['name'], 'testTaxiAdd')
        self.assertFalse(hasattr(tc1, 'failure'))

        tc2 = testcases[4]
        self.assertEqual(tc2['name'], 'taxiAllGetOutTaxiNotEmpty')
        failure = tc2['failure']
        self.assertEqual(failure['type'], 'junit.framework.AssertionFailedError')
        self.assertIn('allGetOut()', failure['message'])
        self.assertIn('allGetOut()', failure['stacktrace'])

        tc3 = testcases[3]
        self.assertEqual(tc3['name'], 'testTaxiDriverAssigned')
        error = tc3['error']
        self.assertEqual(error['type'], 'java.lang.IllegalArgumentException')
        self.assertEqual('Sample message', error['message'])
        self.assertIn('Exception: Sample message', error['stacktrace'])

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            junit.xml_to_dict('<invalid-root />')

    def test_no_testcases(self):
        ts = junit.xml_to_dict('<testsuite><system-out /><system-err /></testsuite>')
        self.assertEqual(len(ts['testcases']), 0)

    def test_missing_systemerr_or_systemout(self):
        documents = [
            '<testsuite><system-err /></testsuite>',
            '<testsuite><system-out /></testsuite>',
            '<testsuite></testsuite>',
        ]
        for document in documents:
            ts = junit.xml_to_dict(document)
            self.assertEqual(len(ts['testcases']), 0)


class StacktraceFilterTest(TestCase):
    def test(self):
        with open(Path(SAMPLES_PATH, 'stacktrace.txt')) as stream:
            stacktrace = stream.read()
        filtered_stacktrace = junit.filter_stacktrace(stacktrace)
        self.assertIn('AssertionFailedError', filtered_stacktrace)
        self.assertIn('TaxiTest.createTaxi(', filtered_stacktrace)
        self.assertIn('TaxiTest.setUp(', filtered_stacktrace)
        self.assertNotIn('jdk.internal.reflect', filtered_stacktrace)
        self.assertNotIn('types.TestClass', filtered_stacktrace)
        self.assertNotIn('constraint.Constraint', filtered_stacktrace)


class XMLBombProtectionTest(TestCase):
    def test_malicious_xmlfile(self):
        with self.assertRaises(ValueError):
            junit.xml_to_dict(MALICIOUS_XML)
