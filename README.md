        ___       ___       ___       ___       ___       ___
       /\  \     /\__\     /\__\     /\  \     /\  \     /\  \
      _\:\  \   /:| _|_   /:/  /    /::\  \   /::\  \   /::\  \
     /\/::\__\ /::|/\__\ /:/__/    /:/\:\__\ /:/\:\__\ /::\:\__\
     \::/\/__/ \/|::/  / \:\  \    \:\/:/  / \:\/:/  / \/\::/  /
      \:\__\     |:/  /   \:\__\    \::/  /   \::/  /     \/__/
       \/__/     \/__/     \/__/     \/__/     \/__/

[![License: GPL v3](https://img.shields.io/badge/license-GPL%20v3-blue.svg)](http://www.gnu.org/licenses/gpl-3.0)
[![Development status: Beta](https://img.shields.io/badge/development%20status-beta-orange.svg)](#)
[![Build Status](https://travis-ci.org/st-tu-dresden/inloop.svg?branch=master)](https://travis-ci.org/st-tu-dresden/inloop)

This is INLOOP, the interactive learning center for object-oriented programming.

INLOOP is a web application based on Django to manage programming assignments for
computer science courses. It uses Docker containers to execute programming task
solutions submitted by students in isolated environments.


## Quick start

Assuming you've met the [dependencies listed below](#dependencies), run the following inside
a shell:

    # setup a virtual environment and activate it
    python3 -m venv .state/venv && source .state/venv/bin/activate

    # install required Python libraries
    pip install -r requirements/main.txt -r requirements/dev.txt

    # initialize the database (uses SQLite locally)
    ./manage.py migrate

    # create a first user with superuser privileges
    ./manage.py createsuperuser

    # run and monitor all required components in developer mode
    # (this also executes unit tests if changes are detected)
    honcho start

The development webserver now runs at <http://127.0.0.1:8000>. Exit `honcho` with `Ctrl-C`.


### Test suite

We use Django standard facilities for testing. All tests reside in the `tests` package and
consist of separate sub-packages for fast unit tests and slower integration tests:

    tests
    ├── docker/
    └── unit/

Executing tests in the `tests.docker` package requires the Docker image to be built once
before:

    cd tests/docker && docker build -t inloop-integration-test .

Examples:

    # run all tests (15 sec)
    ./manage.py test

    # run unit tests only (3 sec)
    ./manage.py test tests.unit


### Dependencies

In general you'll need:

* Git >= 2.3
* Python >= 3.4
* Docker >= 1.10
* Redis >= 2.6
* Optional: tools and libraries to build Python extensions (for psycopg2)
* Optional: node.js and npm (to rebuild CSS and Javascript bundles)

Platform specific instructions:

* Ubuntu >= 14.04 and Debian >= 8:

        sudo apt-get install build-essential git libpq-dev nodejs npm python3 python3-dev redis-server

        sudo apt-get install python3-venv || sudo apt-get install python3.4-venv

  For some silly reason I dare not explain here, on Ubuntu/Debian the `node` command is called
  `nodejs` and you have to symlink it as follows in order to get `make assets` to work.

        sudo ln -s /usr/bin/nodejs /usr/local/bin/node

* Mac OS X using Homebrew:

        brew install node python3 redis


#### Docker setup on Mac OS X

Install Docker for Mac as described on https://docs.docker.com/docker-for-mac/.


#### Docker setup on Ubuntu/Debian

The `docker.io` package shipped with Ubuntu and Debian is usually too old. Install
from the upstream Docker APT repositories instead:

* Ubuntu: https://docs.docker.com/engine/installation/linux/ubuntulinux/
* Debian: https://docs.docker.com/engine/installation/linux/debian/

Ensure you have at least Docker version 1.10 by checking the output of

    docker --version

INLOOP depends on the `--memory` option to limit memory available to a container.
If you have followed the linked installation docs carefully, running

    grep -o swapaccount=1 /proc/cmdline

should print

    swapaccount=1

If not, you need to update your GRUB config to add the `swapaccount=1` param to your
kernel command line and reboot (see the linked Docker docs for details).

Finally run

    docker run hello-world

to verify you can connect to the Docker daemon.


## Further documentation

* [Contributor's guide](CONTRIBUTING.md)
* [Deployment guide](docs/deployment-guide.md)
* [Building CSS and Javascript bundles](docs/static-assets.md)


## Authors and credits

**Project lead**: Martin Morgenstern<br>
**Junior programmer**: Dominik Muhs

INLOOP borrows its concept from the Praktomat, developed originally at the
University of Passau and later at the Karlsruhe Institute of Technology:

* http://pp.ipd.kit.edu/projects/praktomat/praktomat.php
* https://github.com/KITPraktomatTeam/Praktomat


## License

INLOOP is released under GPL version 3.

    Copyright (C) 2015-2016 Dominik Muhs and Martin Morgenstern
    Economic rights: Technische Universität Dresden (Germany)

    INLOOP is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    INLOOP is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
