from django.utils.functional import cached_property

from inloop.solutions.prettyprint.tools import Renderable


class Alert:
    """
    Represent a message, error, failure, hint...
    that can occur during a code quality check.
    """

    def __init__(self, description):
        """
        Create an alert

        Args:
            description (str): The description of the alert.
        """
        self.description = description


class CompositeAlert(Alert):
    """
    Represent an alert, which can contain other alerts.

    Can be used to fold multiple alerts into tree structures.
    """
    def __init__(self, description, components):
        """
        Create a composite alert.

        Args:
            description (str): The description of the alert itself.
            components (list): The optional list of subordinal alerts.
        """
        self.components = components
        super().__init__(description)

    def append(self, alert):
        """
        Add a subordinal alert to the
        components of the composite alert.
        """
        self.components.append(alert)


class FileAlert(Alert):
    """
    Represent an alert, which specifically points to a file.

    Use file alerts to point out specific files, or specific
    positions (only a line, or both a line and a column) in files.
    """

    class File:
        """
        Define a structure of a file to be provided in a file alert.
        """
        def __init__(self, file_name, file_contents):
            """
            Create a file.

            Args:
                file_name (str): The file name.
                file_contents (str): The file contents.
            """
            self.file_name = file_name
            self.file_contents = file_contents

    class Line:
        """
        Define a structure of a line in a file.
        """
        def __init__(self, line_number, line_contents):
            """
            Create a line.

            Args:
                 line_number (int): The line number.
                 line_contents (str): The contents of the line.
            """
            self.line_number = line_number
            self.line_contents = line_contents

    def __init__(self, description, file, line_number=None, column_number=None):
        """
        Create a file alert.

        Args:
            description (str): The description of the alert.
            file (FileAlert.File): The file to be pointed out.
            line_number (int): An optional line number in the given file.
            column_number (int): An optional column number in the given file.
        """
        super().__init__(description)
        self.file = file
        self.line_number = line_number
        self.column_number = column_number

    @cached_property
    def file_lines(self):
        """
        Split the given file into lines.

        Returns:
            list: The list of lines in the given file.
        """
        return self.file.file_contents.splitlines()

    @cached_property
    def highlighted_line(self):
        """
        Extract the line, which is given by the line number.

        Returns:
            FileAlert.Line: The extracted line.
        """
        try:
            return FileAlert.Line(self.line_number, self.file_lines[self.line_number])
        except (TypeError, IndexError):
            return None


class CheckstyleAlert(FileAlert, Renderable):
    """
    Adapt the file alert to the checkstyle format.

    Uses the mixin Renderable to provide a way to
    render checkstyle alerts in place.
    """

    template_name = "solutions/prettyprint/alerts/checkstyle_alert.html"

    def __init__(self, description, file, line_number=None, column_number=None, severity=None):
        """
        Create a checkstyle alert.

        Args:
            description (str): A description of the alert.
            file (CheckstyleAlert.File): The file on which checkstyle detected issues.
            line_number (int): An optional line number in the given file.
            column_number (int): An optional column number in the given file.
            severity (str): The severity of the detected issue.
        """
        super().__init__(description, file, line_number, column_number)
        self.severity = severity


class TestCaseAlert(Alert, Renderable):
    """
    Adapt the alert to the jUnit test case format.

    Uses the mixin Renderable to provide a way to
    render jUnit test case alerts in place.
    """

    template_name = "solutions/prettyprint/alerts/test_case_alert.html"

    class Complaint:
        """
        Represents a complaint in a jUnit test case,
        which can be either a failure or an error.

        Failures and errors have the same attributes and are
        only distinguished by their names and by their severities.
        """
        def __init__(self, message, exception_type, stacktrace):
            """
            Create a complaint.

            Args:
                message (str): The complaint message.
                exception_type (str): The type of exception, which was thrown.
                stacktrace (str): The detailed stacktrace of the exception.
            """
            self.message = message
            self.exception_type = exception_type
            self.stacktrace = stacktrace

    def __init__(self, description, name, time, errors=None, failures=None):
        """
        Create a test case alert.

        Args:
            description (str): The description of the test case.
            name (str): The name of the test case.
            time (float): The time elapsed during the processing of the test case in seconds.
            errors (list): The list of complaints, which are declared as errors.
            failures (list): The list of complaints, which are declared as failures.
        """
        super().__init__(description=description)
        self.name = name
        self.time = time
        self.errors = errors
        self.failures = failures

    @cached_property
    def did_pass(self):
        """
        Determine if the test case passed.

        Returns:
            bool: True if the test case passed, False otherwise.
        """
        return not self.errors and not self.failures


class TestSuiteAlert(CompositeAlert, Renderable):
    """
    Adapt the composite alert to the jUnit test suite format.

    Uses the mixin Renderable to provide a way to
    render jUnit test case alerts in place. A jUnit
    test suite consists of subordinal test cases.
    """

    template_name = "solutions/prettyprint/alerts/test_suite_alert.html"

    def __init__(
        self, name, errors, failures, skipped, tests, time, components,
        system_out=None, system_err=None
    ):
        """
        Create a test suit alert.

        Args:
            name (str): The name of the test suite.
            errors (int): The number of errors that occured in all subordinal test cases.
            failures (int): The number of failures that occured in all subordinal test cases.
            skipped (int): The number of subordinal test cases, which were skipped.
            tests (int): The total number of subordinal test cases.
            time (float): The time elapsed during the processing of the test suite.
            components (list): The optional list of subordinal test case alerts.
            system_out (str): The test suite stdout output.
            system_err (str): The test suite stderr output.
        """
        super().__init__(description=name, components=components)
        self.name = name
        self.errors = errors
        self.failures = failures
        self.skipped = skipped
        self.tests = tests
        self.time = time
        self.system_out = system_out
        self.system_err = system_err

    @cached_property
    def passed(self):
        """
        Determine how many test cases in the test suite passed.

        Returns:
            int: The number of passed test cases.
        """
        return self.tests - self.failures
