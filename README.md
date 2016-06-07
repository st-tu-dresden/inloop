        ___       ___       ___       ___       ___       ___
       /\  \     /\__\     /\__\     /\  \     /\  \     /\  \
      _\:\  \   /:| _|_   /:/  /    /::\  \   /::\  \   /::\  \
     /\/::\__\ /::|/\__\ /:/__/    /:/\:\__\ /:/\:\__\ /::\:\__\
     \::/\/__/ \/|::/  / \:\  \    \:\/:/  / \:\/:/  / \/\::/  /
      \:\__\     |:/  /   \:\__\    \::/  /   \::/  /     \/__/
       \/__/     \/__/     \/__/     \/__/     \/__/

This is INLOOP, the interactive learning center for object-oriented programming.

INLOOP is a web application based on Django to manage programming assignments for
computer science courses. It uses Docker containers to execute programming task
solutions submitted by students in isolated environments.


## Quick start

Assuming you've met the [dependencies listed below](#dependencies), run the following inside
the shell:

    # setup a virtual environment and activate it
    pyvenv venv && source venv/bin/activate

    # install required Python libraries
    pip install -r requirements/development.txt

    # initialize the database (uses SQLite locally)
    ./manage.py migrate

    # create a first user with superuser privileges
    ./manage.py createsuperuser

    # run and monitor all required components in developer mode
    honcho start

The development webserver now runs at <http://127.0.0.1:8000>. Exit `honcho` with `Ctrl-C`.


### Test suite

Use one of the following equivalent commands to run the test suite:

    make test

or

    ./manage.py test

You'll need to build the Docker test image once before with:

    make docker-image


### Dependencies

In general you'll need:

* Git >= 2.3
* Python >= 3.3
* Docker >= 1.10
* Redis >= 2.6
* Tools and libraries to build Python extensions (for Pillow and optionally psycopg2)
* Optional: node.js and npm (to rebuild CSS and Javascript bundles)

Platform specific instructions:

* Ubuntu >= 14.04 and Debian >= 8:

        sudo apt-get install build-essential git libfreetype6-dev libjpeg8-dev liblcms2-dev libpq-dev libtiff5-dev libwebp-dev nodejs npm python3 python3-dev redis-server tcl8.5-dev tk8.5-dev zlib1g-dev

        sudo apt-get install python3-venv || sudo apt-get install python3.4-venv

  For some silly reason I dare not explain here, on Ubuntu/Debian the `node` command is called
  `nodejs` and you have to symlink it as follows in order to get `make assets` to work.

        sudo ln -s /usr/bin/nodejs /usr/local/bin/node

  The same is true for `pyvenv`, which on Ubuntu 14.04 is called `pyvenv-3.4`. I recommend to
  symlink it as well:

        sudo ln -s /usr/bin/pyvenv-3.4 /usr/local/bin/pyvenv

* Mac OS X using Homebrew:

        brew install docker docker-machine node python3 redis


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

If not, you need update your GRUB config to add the `swapaccount=1` param to your
kernel command line and reboot (see the linked Docker docs for details).

Finally run

    docker run hello-world

to verify you can connect to the Docker daemon.


## Further documentation

* [Contributor's guide](CONTRIBUTING.md)
* [Deployment HOWTO](docs/deployment-guide.md)
* [Building CSS and Javascript bundles](docs/static-assets.md)


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
