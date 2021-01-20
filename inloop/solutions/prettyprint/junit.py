"""
Tools and infrastructure to convert XML to template-friendly dicts.

Numerous tools such as Ant, Maven and Gradle produce test reports
according to this format, which is described as XML DTD in the
Javadoc for the class

    org.apache.tools.ant.taskdefs.optional.junit.XMLConstants

which is part of Ant (see https://github.com/apache/ant).
"""
import re
from typing import Any, Dict, Iterable, Optional, Union
from xml.etree.ElementTree import Element

from django.db.models import Manager, QuerySet

from defusedxml import ElementTree as ET


def checkeroutput_filter(queryset: Union[QuerySet, Manager]) -> Iterable[str]:
    """
    Return a list of XML reports filtered from the CheckerOutput queryset.

    The filter takes advantage of the fact that all XML reports comply to
    a specific pattern.
    """
    return queryset.filter(name__startswith="TEST-", name__endswith=".xml").values_list(
        "output", flat=True
    )


def xml_to_dict(xml_report: str) -> Dict[str, Any]:
    """Parse the given JUnit XML string and return a dict representation."""
    return testsuite_to_dict(ET.fromstring(xml_report))


def testsuite_to_dict(testsuite: Element) -> Dict[str, Any]:
    """Return a dict representation of the given <testsuite/> Element."""
    if testsuite.tag != "testsuite":
        raise ValueError("The root tag must be a <testsuite/>.")
    ts = dict(testsuite.attrib)
    for key in ["failures", "errors"]:
        ts[key] = int(ts.get(key, 0))
    ts["testcases"] = [testcase_to_dict(testcase) for testcase in testsuite.findall("testcase")]
    ts["total"] = len(ts["testcases"])
    ts["passed"] = ts["total"] - ts["failures"] - ts["errors"]
    ts["system_out"] = get_text_safe(testsuite.find("system-out"))
    ts["system_err"] = get_text_safe(testsuite.find("system-err"))
    return ts


def get_text_safe(element: Optional[Element]) -> Optional[str]:
    """Return the element's text attribute if possible, otherwise None."""
    if element is not None:
        return element.text
    return None


def testcase_to_dict(testcase: Element) -> Dict[str, Any]:
    """Return a dict representation of the given <testcase/> Element."""
    testcase_dict = dict(testcase.attrib)
    for tag in ["failure", "error"]:
        element = testcase.find(tag)
        if element is not None:
            element_dict = dict(element.attrib)
            element_dict["stacktrace"] = filter_stacktrace(element.text)
            testcase_dict[tag] = element_dict
    return testcase_dict


IGNORE_LINE_REGEXES = [
    # JDK internal classes, mostly Reflection API
    re.compile(r"at java\.base/jdk\.internal"),
    # Our Kotlin-based StructAssert library, which doesn't
    # have a top-level package at the moment.
    # Bandaid solution: detect using the file extension.
    re.compile(r"\(\w+\.kt:\d+\)"),
]


def filter_stacktrace(trace: str) -> str:
    """
    Clean the stracktrace from JDK and StructAssert internals.
    Filtering of JDK lines is necessary because Ant doesn't filter
    "new style" stack trace lines that contain the module name.
    """
    return "\n".join(line for line in trace.splitlines() if not filter_line(line))


def filter_line(line: str) -> bool:
    """Return True if the line should be filtered."""
    return any(regex.search(line) for regex in IGNORE_LINE_REGEXES)
