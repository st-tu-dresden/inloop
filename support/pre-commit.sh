#!/bin/sh
flake8 .
./manage.py test
