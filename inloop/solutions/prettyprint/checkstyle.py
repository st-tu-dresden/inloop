from defusedxml import ElementTree as ET


class CheckstyleData:

    def __init__(self, checkstyle_context, solution_files):
        if checkstyle_context is None:
            raise ValueError('Checkstyle context must not be empty!')
        if solution_files is None:
            raise ValueError('Solution files must not be empty!')

        self.files = extract_items_by_key(data=checkstyle_context, key='file')
        self.files = assign_sources_to_files(self.files, solution_files)
        self.files = assign_code_to_errors(self.files)
        self.files = assign_grouped_errors(self.files)
        self.files = remove_input_path(self.files)

        self.total_errors = sum(
            [len(file['checkstyle_errors']) for file in self.files]
        )
        self.total_warnings = sum(
            [len(file['checkstyle_warnings']) for file in self.files]
        )
        self.total_issues = self.total_warnings + self.total_errors

    def __repr__(self):
        return f'<CheckstyleDict {self.files}>'


def extract_items_by_key(*, data, key):
    """
    Recursive function to extract a list of items from a given dictionary by key.
    Searches the given dictionary recursively and adds every value that is
    assigned to a key that corresponds to the parameter key.

    Args:
        data: The input dictionary, list or value.
        key (str): Extract this key from the dictionary.

    Returns:
        list: A list of all elements that correspond to the given key.

    """
    values = []
    if isinstance(data, dict):
        try:
            tag = data['tag']
            children = data['children']
        except KeyError:
            return values
        if tag == key:
            values.append(data)
        for child in children:
            values += extract_items_by_key(data=child, key=key)
    elif isinstance(data, list):
        for ele in data:
            values += extract_items_by_key(data=ele, key=key)
    return values


def xml_strings_from_testoutput(*, testoutput_set, startswith, endswith):
    """
    Generate context for the solution file passed on initialization.

    Args:
        testoutput_set : The testoutput set
        startswith (str): Filter the testoutput set by this start string.
        endswith (str): Filter the testoutput set by this end string.

    Returns:
        list: The extracted xml-strings.

    """
    filtered_set = testoutput_set.filter(
        name__startswith=startswith,
        name__endswith=endswith
    )
    flattened_set = filtered_set.values_list('output', flat=True)
    return flattened_set


def context_from_xml_strings(*, xml_strings, filter_keys):
    """
    Generate context from the parsed xml strings.

    Args:
        xml_strings(list): The xml strings to be parsed
        filter_keys(list): Filter the xml strings by these keys.

    Returns:
        list: The context.

    """
    context = []
    for xml_string in xml_strings:
        try:
            element_tree = ET.fromstring(xml_string)
            context.append(element_tree.attrib)
        except (ValueError, ET.ParseError):
            continue
        context.append(
            element_tree_to_dict(element_tree, filter_keys)
        )
    return context


def element_tree_to_dict(tree, filter_keys):
    """
    Recursive function to filter and transform defusedxml.ElementTree to dicts.

    Args:
        tree (ElementTree): The input ElementTree.
        filter_keys (list): Filters the tree by a list of strings.

    Returns:
        dict: The filtered and transformed ElementTree as a dict.

    """
    if filter_keys:
        children = [
            child for child in tree.getchildren() if child.tag in filter_keys
        ]
    else:
        children = tree.getchildren()
    return {
        'tag': tree.tag,
        'attrib': tree.attrib,
        'text': tree.text,
        'children': [
            element_tree_to_dict(child, filter_keys)
            for child in children
        ],
    }


def assign_sources_to_files(checkstyle_files, solution_files):
    """
    Assign source code to files by name similarity.

    Args:
        checkstyle_files (list): The input files list.
        solution_files: The solution file set.

    Returns:
        list: The checkstyle_files with assigned source code.
    """
    for f in checkstyle_files:
        file_paths = f['attrib']['name'].split('/')
        if file_paths:
            file_name = file_paths[-1]
            for solution_file in solution_files:
                if solution_file.name == file_name:
                    f['source'] = solution_file.contents
                    break
    return checkstyle_files


def assign_code_to_errors(checkstyle_files):
    """
    Assign source code to their errors by splitting
    the file source code in lines.

    Args:
        checkstyle_files (list): The input files list.

    Returns:
        list: The checkstyle_files list with assigned code lines.
    """
    for f in checkstyle_files:
        source_split = f['source'].splitlines()
        # Insert empty code line on top to match Checkstyle output
        # since the 1st code line is the line in source_split
        # with the index 0. We shift the list by 1.
        source_split.insert(0, '\n')
        for error in [e for e in f['children'] if e['tag'] == 'error']:
            error['code'] = source_split[int(error['attrib']['line'])]
    return checkstyle_files


def assign_grouped_errors(checkstyle_files):
    """
    Groups checkstyle error types (warning, error) and adds
    them to the checkstyle_files list.

    Args:
        checkstyle_files (list): The input files list.

    Returns:
        list: The checkstyle_files with grouped errors.
    """
    for f in checkstyle_files:
        f['checkstyle_errors'] = [
            e for e in f['children'] if e['attrib']['severity'] == 'error'
        ]
        f['checkstyle_warnings'] = [
            e for e in f['children'] if e['attrib']['severity'] == 'warning'
        ]
        f['total_checkstyle_errors'] = len(f['checkstyle_errors'])
        f['total_checkstyle_warnings'] = len(f['checkstyle_warnings'])
    return checkstyle_files


def remove_input_path(checkstyle_files, input_path='/checker/input/'):
    """
    Removes the input path from the checkstyle_files list.

    Args:
        checkstyle_files (list): The input files list.
        input_path (str): The input path.

    Returns:
        list: The checkstyle_files with modified input paths.
    """
    for f in checkstyle_files:
        f['attrib']['name'] = f['attrib']['name'].replace(input_path, '')
    return checkstyle_files
