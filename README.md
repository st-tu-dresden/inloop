# INLOOP

This is INLOOP, an interactive learning center for object-oriented programming.

## Getting started

This file contains instructions to quickly set up a developer environment.
Please also have a look at the documentation provided for

* [contributors](docs/developer-guide.md) and
* [administrators](docs/deployment-guide.md).

### Prerequisites

#### Python 3

INLOOP only runs on Python 3 and refuses to run on anything older than that.
We recommend to use the latest 3.x branch, which currently is Python 3.4 and
already bundles `pip` and `pyvenv` (aka `virtualenv`).

#### Platform

We use a Debian-based Linux and Mac OS X during development. Windows is not
supported.

For deployment, we recommend to use Ubuntu 12.04 or 14.04.

Note: Ubuntu 12.04 only ships with Python 3.2, which means you should install
a more recent version (see the `Vagrantfile`).

#### Tools and libraries

You'll at least need:

* Tools to build Python extensions (e.g., required by Pillow and psycopg2)
    * Build tools (`gcc`/`clang`, `make`)
    * The `python3-dev` package (Python 3 development files)
* For Pillow: `libtiff4-dev libjpeg8-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev tcl8.5-dev tk8.5-dev`
* libpq header files (for psycopg2)

If you use a Debian-based Linux, take a look at the `Vagrantfile` to get a
list of packages you need to install.

### Local development setup

Assuming you already cloned this repository and changed to the directory:

```bash
# setup a virtual environment ...
pyvenv venv

# ... and activate it
source venv/bin/activate

# install required Python libraries
pip install -r requirements_dev.txt

# initialize the database (uses SQLite locally)
./manage.py migrate

# create a first user with superuser privileges
./manage.py createsuperuser

# run Django's integrated development webserver
./manage.py runserver
```

### Working on static assets (CSS and Javascript)

The minified static asset bundles are part of the clone for convenience and
there is no need to build them *unless* you want to add custom styles or
Javascript.

We use several third-party LESS/CSS and Javascript frameworks which are
included as git submodules under the `vendor` directory. That means, the
first step is to run

    git submodule update --init

Our own LESS and Javascript source files reside in the `js` and `less`
directories. Everything is combined into one minified CSS and one minified
Javascript file in subdirectories of `inloop/core/static`. The combined
files are generated using the `Makefile` as follows:

    make assets

You may also run

    make watch

which will watch for changes in the source files and run `make assets`
as necessary. The `Makefile` depends on `nodejs` and `npm`.

### Using the vagrant box

The `Vagrantfile` describes a box which resembles the production setup very
closely and can be used for integration tests. Use `vagrant up` to build the
box (the first time, this will take a while).

As an example, to execute the testsuite in the box, use:

```bash
vagrant ssh
cd /vagrant
pip install -r requirements_all.txt
./manage.py test
```
