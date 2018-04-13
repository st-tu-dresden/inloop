"""
Tools and infrastructure to convert XML to template-friendly dicts.

Numerous tools such as Ant, Maven and Gradle produce test reports
according to this format, which is described as XML DTD in the
Javadoc for the class

    org.apache.tools.ant.taskdefs.optional.junit.XMLConstants

which is part of Ant (see https://github.com/apache/ant).
"""
from defusedxml import ElementTree as ET


class XMLContextParser(object):
    STARTSWITH = {
        "junit": "TEST-",
        "checkstyle": "checkstyle",
    }

    ENDSWITH = {
        "junit": ".xml",
        "checkstyle": ".xml",
    }

    def __init__(self, *, solution):
        result = solution.testresult_set.last()
        self.testoutput_set = result.testoutput_set

    def __str__(self):
        return "<XMLParser object with testoutput set: {}>".format(self.testoutput_set)

    def __repr__(self):
        return self.__str__()

    def context(self, *, startswith, endswith, filter_keys):
        filtered_set = self.testoutput_set.filter(name__startswith=startswith, name__endswith=endswith)
        flattened_set = filtered_set.values_list("output", flat=True)
        context = []
        for xml_string in flattened_set:
            # throws element_tree.ParseError, ValueError
            element_tree = ET.fromstring(xml_string)
            context.append(XMLContextParser.element_tree_to_dict(element_tree, filter_keys))
        return context

    @staticmethod
    def element_tree_to_dict(tree, filter_keys):
        if filter_keys:
            children = [child for child in tree.getchildren() if child.tag in filter_keys]
        else:
            children = tree.getchildren()
        if children:
            return {tree.tag: [XMLContextParser.element_tree_to_dict(child, filter_keys) for child in children]}
        else:
            if tree.attrib is not None:
                return {tree.tag: tree.attrib}
            else:
                return {tree.tag: tree.text}


def checkeroutput_filter(queryset, filter_type="junit"):
    """
    Return a list of XML reports filtered from the CheckerOutput queryset.

    Currently supported output types:
    - junit
    - checkstyle

    The filter takes advantage of the fact that all XML reports comply to
    a specific pattern.
    """

    if filter_type == "junit":
        return queryset.filter(
            name__startswith="TEST-",
            name__endswith=".xml"
        ).values_list("output", flat=True)
    elif filter_type == "checkstyle":
        return queryset.filter(
            name__startswith="checkstyle",
            name__endswith=".xml"
        ).values_list("output", flat=True)
    else:
        raise ValueError("The checkeroutput filter type must be \"junit\" or \"checkstyle\".")


def xml_to_dict(xml_report, xml_type="junit"):
    """Parse the given JUnit or checkstyle XML string and return a dict representation."""
    if xml_type == "junit":
        return testsuite_to_dict(ET.fromstring(xml_report))
    elif xml_type == "checkstyle":
        return checkstyle_to_dict(ET.fromstring(xml_report))
    else:
        raise ValueError("The xml type must be \"junit\" or \"checkstyle\".")


def testsuite_to_dict(testsuite):
    """Return a dict representation of the given <testsuite/> Element."""
    if testsuite.tag != "testsuite":
        raise ValueError("The root tag must be a <testsuite/>.")
    ts = dict(testsuite.attrib)
    for key in ["failures", "errors"]:
        ts[key] = int(ts.get(key, 0))
    ts["testcases"] = [
        testcase_to_dict(testcase) for testcase in testsuite.findall("testcase")
    ]
    ts["total"] = len(ts["testcases"])
    ts["passed"] = ts["total"] - ts["failures"] - ts["errors"]
    ts["system_out"] = get_text_safe(testsuite.find("system-out"))
    ts["system_err"] = get_text_safe(testsuite.find("system-err"))
    return ts


def checkstyle_to_dict(checkstyle):
    """Return a dict representation of the given <checkstyle/> Element."""
    if checkstyle.tag != "checkstyle":
        raise ValueError("The root tag must be a <checkstyle/>.")
    cs = dict(checkstyle.attrib)
    cs["files"] = [
        {
            file.attrib["name"]: [
                error.attrib
                for error in file.findall("error")
            ]
        }
        for file in checkstyle.findall("file")
    ]
    return cs


def get_text_safe(element):
    """Return the element's text attribute if possible, otherwise None."""
    if element is not None:
        return element.text
    return None


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
