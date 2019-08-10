from abc import ABC, abstractmethod

from django.utils.functional import cached_property

from defusedxml import minidom

from inloop.solutions.prettyprint.alerts import CheckstyleAlert, TestCaseAlert, TestSuiteAlert


class AbstractAlertGenerator(ABC):
    """
    Use as a abstract base class generator for alerts.

    This class can be extended to provide an adapter
    to third party output data formats.
    """
    def __iter__(self):
        return self.alerts

    @abstractmethod
    @cached_property
    def alerts(self):
        """
        Generate all alerts.

        Use as the entry point to parse alerts from
        a third party data format.
        """
        raise NotImplementedError


class BaseXMLStringAlertGenerator(AbstractAlertGenerator):
    """
    Use as a generator for alerts.

    Provide a base for generators, which parse an xml string.
    """
    def __init__(self, xml_string):
        """
        Create a base xml string alert generator.

        The base xml string alert generator parses the given xml
        string into a DOM object, which can then be parsed efficiently.
        The DOM object is stored under xml_document.

        Raises:
            defusedxml.common.EntitiesForbidden if the string contains forbidden entities.

        Args:
            xml_string (str): The XML string to be parsed.
        """
        self.xml_document = minidom.parseString(xml_string)

    @cached_property
    def alerts(self):
        """
        Generate all alerts.

        Use as the entry point to parse alerts from
        a third party data format.
        """
        return super().alerts


class CheckstyleAlertGenerator(BaseXMLStringAlertGenerator):
    """
    Adapt the checkstyle xml output format.
    """
    def __init__(self, xml_string, solution_files):
        """
        Create a checkstyle alert generator.

        Args:
            xml_string (str): The checkstyle XML string to be parsed.
            solution_files (list): The list of solution files that were checked.
        """
        super().__init__(xml_string)
        self.solution_files = solution_files

    @cached_property
    def alerts(self):
        """
        Generate all checkstyle alerts.

        The checkstyle xml format contains multiple file nodes.
        Each of these file nodes corresponds to a file in the
        submitted solution. To show line specific alerts,
        the solution files and the checkstyle output file
        nodes have to be matched. After matching, a checkstyle
        alert is created for all subordinal error nodes.
        The error node attributes contain a error message,
        and optionally a severity, a line and a column.

        Returns:
            The generator object, which generates all checkstyle alerts.
        """
        file_nodes = self.xml_document.getElementsByTagName("file")

        for solution_file in self.solution_files:

            for file_node in file_nodes:

                file_name = file_node.attributes["name"].value
                # Remove checker input path to match the
                # solution file name with the file node name
                file_name = file_name.replace("/checker/input/", "")

                if solution_file.name != file_name:
                    continue

                file = CheckstyleAlert.File(file_name, solution_file.contents)

                for node in file_node.getElementsByTagName("error"):
                    description = node.attributes["message"].value
                    try:
                        severity = node.attributes["severity"].value
                    except KeyError:
                        severity = None
                    try:
                        line_number = int(node.attributes["line"].value)
                    except (KeyError, ValueError):
                        line_number = None
                    try:
                        column_number = int(node.attributes["column"].value)
                    except (KeyError, ValueError):
                        column_number = None

                    yield CheckstyleAlert(
                        description=description, file=file,
                        line_number=line_number, column_number=column_number,
                        severity=severity
                    )


class JUnitAlertGenerator(BaseXMLStringAlertGenerator):
    """
    Adapt the jUnit xml output format.
    """

    @cached_property
    def alerts(self):
        """
        Generate all test suite alerts.

        The jUnit xml format contains multiple test suite nodes.
        Each of these test suite nodes is parsed into a
        test suite alert. The test suite nodes contain multiple
        test case nodes, which are parsed into test case alerts
        and subsequently linked to the test suite alert.
        A test case can have the following states: passed,
        failed and errored. If a test case failed or errored,
        the corresponding node contains failure or error nodes.
        These are parsed into complaints and passed to the test
        case alert on creation.

        Returns:
            The generator object, which generates all test suite alerts.
        """
        for test_suite_node in self.xml_document.getElementsByTagName("testsuite"):

            system_out_nodes = test_suite_node.getElementsByTagName("system-out")
            system_err_nodes = test_suite_node.getElementsByTagName("system-err")
            system_out = "\n".join(n.firstChild.nodeValue for n in system_out_nodes
                                   if n.firstChild is not None)
            system_err = "\n".join(n.firstChild.nodeValue for n in system_err_nodes
                                   if n.firstChild is not None)

            test_suite_alert = TestSuiteAlert(
                name=test_suite_node.attributes["name"].value,
                errors=int(test_suite_node.attributes["errors"].value),
                failures=int(test_suite_node.attributes["failures"].value),
                skipped=int(test_suite_node.attributes["skipped"].value),
                tests=int(test_suite_node.attributes["tests"].value),
                time=float(test_suite_node.attributes["time"].value),
                system_out=system_out,
                system_err=system_err,
                components=[]
            )

            for test_case_node in test_suite_node.getElementsByTagName("testcase"):

                class_name = test_case_node.attributes["classname"].value
                name = test_case_node.attributes["name"].value
                time = float(test_case_node.attributes["time"].value)
                description = "{}.{}".format(
                    class_name, name
                )

                failures = [
                    TestCaseAlert.Complaint(
                        n.attributes["message"].value,
                        n.attributes["type"].value,
                        n.firstChild.nodeValue
                    )
                    for n in test_case_node.getElementsByTagName("failure")
                ]

                errors = [
                    TestCaseAlert.Complaint(
                        n.attributes["message"].value,
                        n.attributes["type"].value,
                        n.firstChild.nodeValue
                    )
                    for n in test_case_node.getElementsByTagName("error")
                ]

                test_case_alert = TestCaseAlert(
                    description=description, name=name, time=time,
                    errors=errors, failures=failures
                )

                test_suite_alert.append(test_case_alert)

            yield test_suite_alert
