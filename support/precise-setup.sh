#!/bin/bash

if [[ ! -d venv ]]; then
    echo >&2 "ERROR: directory 'venv' not found in $PWD."
    echo >&2 "Please execute this script at the project root and make"
    echo >&2 "sure the virtualenv is installed in <project_root>/venv"
    exit 1
fi

. /etc/lsb-release

if [[ $DISTRIB_CODENAME != "precise" ]]; then
    echo >&2 "ERROR: apparently not on Ubuntu 12.04, exiting..."
    exit 1
fi

# o Installs Ubuntu-packaged version of psycopg2, which avoids the
#   many quirks needed to build it from source on this distro.
# o Installs build deps for Pillow (which builds fine w/o h4cks)
sudo aptitude -R install build-essential python3-psycopg2 python3-dev libjpeg-dev zlib1g-dev

# Import postgres packages into our virtualenv.
cd venv/lib/python3.2/site-packages && \
    ln -s /usr/lib/python3/dist-packages/psycopg2* .

exit $?
