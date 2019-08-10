import os
import shutil
from tempfile import mkdtemp

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings, tag

import defusedxml

from inloop.solutions.models import SolutionFile
from inloop.solutions.prettyprint.alerts import TestSuiteAlert
from inloop.solutions.prettyprint.generators import (AbstractAlertGenerator,
                                                     BaseXMLStringAlertGenerator,
                                                     CheckstyleAlertGenerator, JUnitAlertGenerator)

from tests.solutions.mixins import SolutionsData

from . import SAMPLES_PATH

with SAMPLES_PATH.joinpath("TEST-TaxiTest.xml").open() as fp:
    JUNIT_SAMPLE_XML = fp.read()

with SAMPLES_PATH.joinpath("billion_laughs.xml").open() as fp:
    MALICIOUS_XML = fp.read()


class AbstractAlertGeneratorTest(TestCase):
    def test_abstract(self):
        """
        Verify that the abstract alert generator
        does not support parsing alerts.
        """
        try:
            AbstractAlertGenerator()
            self.fail("Abstract alert generator should be abstract")
        except TypeError:
            pass


class BaseXMLStringAlertGeneratorTest(TestCase):
    def setUp(self):
        super().setUp()
        self.xml = '<?xml version="1.0" encoding="UTF-8"?><test></test>'
        self.generator = BaseXMLStringAlertGenerator(self.xml)

    def test_xml_parsing(self):
        """
        Verify that the base xml string generator parses xml
        correctly into a DOM object.
        """
        self.assertIsNotNone(self.generator.xml_document)
        self.assertEqual(len(self.generator.xml_document.getElementsByTagName("test")), 1)

    def test_alerts_unsupported(self):
        """
        Verify that the alerts property is unsupported on the
        base generator. The base generator should not be used directly.
        """
        try:
            _ = self.generator.alerts
            self.fail("The base xml string generator should not support direct usage.")
        except NotImplementedError:
            pass


@tag("slow")
class MaliciousXMLTest(TestCase):
    def test_malicious_xml(self):
        """
        Verify that the base xml string alert generator fails to create
        when malicious xml is passed to it.
        """
        try:
            BaseXMLStringAlertGenerator(MALICIOUS_XML)
            self.fail("Malicious xml should not be parsed")
        except defusedxml.common.EntitiesForbidden:
            pass


TEST_MEDIA_ROOT = mkdtemp()


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class CheckstyleAlertGeneratorTest(SolutionsData, TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not os.path.isdir(TEST_MEDIA_ROOT):
            os.makedirs(TEST_MEDIA_ROOT)

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        with SAMPLES_PATH.joinpath("checkstyle.xml").open() as f:
            cls.checkstyle_xml = f.read()
        with SAMPLES_PATH.joinpath("Fibonacci.java").open() as f:
            cls.fibonacci = f.read()
            cls.solution_file = SolutionFile.objects.create(
                solution=cls.passed_solution,
                file=SimpleUploadedFile('Fibonacci.java', cls.fibonacci.encode())
            )
        cls.missing_solution_file = SolutionFile.objects.create(
            solution=cls.passed_solution,
            file=SimpleUploadedFile('Missing.java', ''.encode())
        )

    def test_checkstyle_alert_generation(self):
        """
        Verify that the checkstyle alert generator
        generates the correct alerts.
        """
        alerts = list(iter(
            CheckstyleAlertGenerator(
                self.checkstyle_xml, [self.solution_file, self.missing_solution_file]
            )
        ))

        self.assertEqual(len(alerts), 3)

        line_numbers = [2, None, 4]
        columns = [1, None, None]
        severities = ["error", "warning", None]
        for alert, line_number, column, severity in zip(
            alerts, line_numbers, columns, severities
        ):
            self.assertEqual(alert.line_number, line_number)
            if line_number is None:
                self.assertIsNone(alert.highlighted_line)
            else:
                self.assertEqual(
                    alert.highlighted_line.line_contents,
                    self.fibonacci.splitlines()[line_number]
                )
            self.assertEqual(alert.column_number, column)
            self.assertEqual(alert.severity, severity)
            self.assertIsNotNone(alert.description)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_MEDIA_ROOT)
        super().tearDownClass()


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class JUnitAlertGeneratorTest(SolutionsData, TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not os.path.isdir(TEST_MEDIA_ROOT):
            os.makedirs(TEST_MEDIA_ROOT)

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        with SAMPLES_PATH.joinpath("TEST-TaxiTest.xml").open() as f:
            cls.junit_xml = f.read()

    def generate_alerts(self):
        alerts = list(iter(
            JUnitAlertGenerator(self.junit_xml)
        ))
        self.assertEqual(len(alerts), 1)
        return alerts[0]

    def test_test_suite_alert_generation(self):
        """
        Verify that the jUnit alert generator
        generates the correct test suite alert.
        """
        test_suite_alert = self.generate_alerts()
        self.assertIsInstance(test_suite_alert, TestSuiteAlert)
        self.assertEqual(test_suite_alert.errors, 0)
        self.assertEqual(test_suite_alert.failures, 1)
        self.assertEqual(test_suite_alert.name, "TaxiTest")
        self.assertEqual(test_suite_alert.skipped, 0)
        self.assertEqual(test_suite_alert.tests, 5)
        self.assertEqual(test_suite_alert.time, 0.119)
        self.assertEqual(test_suite_alert.passed, 4)
        self.assertFalse(test_suite_alert.system_err)
        self.assertIsNotNone(test_suite_alert.system_out)

    def test_test_case_alert_generation(self):
        """
        Verify that the jUnit alert generator
        generates the correct test case alerts.
        """
        test_suite_alert = self.generate_alerts()
        names = ["testTaxiAdd", "testHuman",
                 "testTaxiAllGetOutEmptyTaxi", "testTaxiDriverAssigned",
                 "taxiAllGetOutTaxiNotEmpty"]
        times = [0.002, 0.0, 0.0, 0.0, 0.015]
        have_failed = [False, False, False, False, True]
        have_errored = [False, False, False, True, False]
        for alert, name, time, has_failed, has_errored in zip(
            test_suite_alert.components, names, times, have_failed, have_errored
        ):
            self.assertEqual(alert.name, name)
            self.assertEqual(alert.time, time)
            self.assertEqual(alert.failures != [], has_failed)
            self.assertEqual(alert.errors != [], has_errored)
            self.assertEqual(alert.did_pass, not has_errored and not has_failed)

    def test_complaints(self):
        """
        Verify that errors and failures are correctly
        parsed by the jUnit alert generator.
        """
        test_suite_alert = self.generate_alerts()
        failed_alert = test_suite_alert.components[4]
        errored_alert = test_suite_alert.components[3]
        self.assertEqual(len(failed_alert.failures), 1)
        self.assertEqual(len(errored_alert.errors), 1)

        failure = failed_alert.failures[0]
        self.assertIn("at TaxiTest.taxiAllGetOutTaxiNotEmpty(TaxiTest.java:102)",
                      failure.stacktrace)
        self.assertIn("expected:<4> but was:<0>", failure.message)
        self.assertIn("junit.framework.AssertionFailedError", failure.exception_type)

        error = errored_alert.errors[0]
        self.assertIn("at Taxi.add(Taxi.java)", error.stacktrace)
        self.assertIn("Sample message", error.message)
        self.assertIn("java.lang.IllegalArgumentException", error.exception_type)

    def test_rendering(self):
        """
        Verify that a test suite is rendered correctly.
        """
        test_suite_alert = self.generate_alerts()
        html = test_suite_alert.rendered
        self.assertIn("TaxiTest", html)
        self.assertIn("at TaxiTest.taxiAllGetOutTaxiNotEmpty(TaxiTest.java:102)", html)
        self.assertIn("Sample message", html)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_MEDIA_ROOT)
        super().tearDownClass()
