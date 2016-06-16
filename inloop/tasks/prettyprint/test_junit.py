from pathlib import Path
from unittest import TestCase

from inloop.tasks.prettyprint import junit


class JUnitXMLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).parent.joinpath("TEST-TaxiTest.xml")
        with path.open(encoding="utf-8") as f:
            cls.SAMPLE_XML = f.read()

    def setUp(self):
        self.ts = junit.xml_to_dict(self.SAMPLE_XML)

    def test_sample_outputs(self):
        self.assertTrue(self.ts["system_out"].startswith("Andrea Bora"))
        self.assertEqual(self.ts["system_err"], None)

    def test_sample_attributes(self):
        self.assertEqual(int(self.ts["errors"]), 0)
        self.assertEqual(int(self.ts["failures"]), 1)
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

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            junit.xml_to_dict("<invalid-root />")

    def test_no_testcases(self):
        ts = junit.xml_to_dict("<testsuite><system-out /><system-err /></testsuite>")
        self.assertEqual(len(ts["testcases"]), 0)
