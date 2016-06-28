"""
Tools and infrastructure to convert JUnit XML to template-friendly dicts.

Numerous tools such as Ant, Maven and Gradle produce test reports
according to this format, which is described as XML DTD in the
Javadoc for the class

    org.apache.tools.ant.taskdefs.optional.junit.XMLConstants

which is part of Ant (see https://github.com/apache/ant).
"""
from xml.etree import ElementTree as ET


def checkeroutput_filter(queryset):
    """
    Return a list of XML reports filtered from the CheckerOutput queryset.

    The filter takes advantage of the fact that all XML reports comply to the
    pattern TEST-*.xml.
    """
    return queryset.filter(
        name__startswith="TEST-",
        name__endswith=".xml"
    ).values_list("output", flat=True)


def xml_to_dict(xml_report):
    """Parse the given JUnit XML string and return a dict representation."""
    return testsuite_to_dict(ET.fromstring(xml_report))


def testsuite_to_dict(testsuite):
    """Return a dict representation of the given <testsuite/> Element."""
    if testsuite.tag != "testsuite":
        raise ValueError("The root tag must be a <testsuite/>.")
    testsuite_dict = dict(testsuite.attrib)
    for key in ["failures", "errors"]:
        testsuite_dict[key] = int(testsuite_dict.get(key, 0))
    testsuite_dict["testcases"] = [
        testcase_to_dict(testcase) for testcase in testsuite.findall("testcase")
    ]
    testsuite_dict["system_out"] = testsuite.find("system-out").text
    testsuite_dict["system_err"] = testsuite.find("system-err").text
    return testsuite_dict


def testcase_to_dict(testcase):
    """Return a dict representation of the given <testcase/> Element."""
    testcase_dict = dict(testcase.attrib)
    for tag in ["failure", "error"]:
        element = testcase.find(tag)
        if element is not None:
            element_dict = dict(element.attrib)
            element_dict["stacktrace"] = element.text
            testcase_dict[tag] = element_dict
    return testcase_dict
