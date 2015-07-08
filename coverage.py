#!/usr/bin/env python
from subprocess import check_call

# modules given to manage.py test:
modules = ['accounts', 'tasks', 'runtimes', 'checker']

check_call(['coverage', 'run', 'manage.py', 'test'] + modules)
check_call(['coverage', 'html'])
