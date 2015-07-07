#!/usr/bin/env python
import sys


def check_commit_line(line_number, line):
    errors = []
    if line_number == 0:
        if line[0].islower():
            errors.append('The first word in the summary line is not capitalized.')
        if len(line) > 50:
            errors.append('The summary line is longer than 50 chars.')

    not_comment = not line.startswith('#')
    if line_number == 1 and not_comment:
        if line.strip() != "":
            errors.append('The second line is not empty.')

    if not_comment:
        if len(line) > 72:
            errors.append('Line {} is longer than 72 chars.'.format(line_number + 1))

    return errors

errors = []
commit_file = sys.argv[1]
with open(commit_file) as f:
    for line_number, line in enumerate(f):
        errors.extend(check_commit_line(line_number, line))
if errors:
    print('Sorry. Your commit message has {} issue(s):'.format(len(errors)))
    for error in errors:
        print('  - {}'.format(error))
    print('The commit message was saved in {}'.format(commit_file))
    sys.exit(len(errors))
