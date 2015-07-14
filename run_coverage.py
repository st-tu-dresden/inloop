#!/usr/bin/env python
from subprocess import check_call

# NOTE: configuration is in .coveragerc
check_call(['coverage', 'run', 'manage.py', 'test'])
check_call(['coverage', 'html'])
