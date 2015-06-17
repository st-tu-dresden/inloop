## Deployment HOWTO

### Overview
This document describes the steps needed for a production setup of INLOOP on
Ubuntu 12.04. Other distros should work in (very) similar ways.

The setup follows current best practices and builds upon the following
components:

* Nginx, acting as a reverse proxy. This is the only service accessible
  from outside. It terminates HTTP and HTTPS connections, handles serving
  static files and routes dynamic requests to the backend.
* Gunicorn, a Python-based application server running the Django application.
* PostgreSQL, an awesome SQL database server.

Why? The Django built-in server and SQLite are of course sufficient during
development. But they are not designed for larger scale and/or production
use. Using the mentioned components offers several advantages, among others
improved security through separation/isolation (each component runs in its
own process with its own user id).

### Prerequisites
* The following guide assumes you already have installed the prerequisites
  mentioned in the [README](README.md), as well as nginx and PostgreSQL.
* We also assume `/srv/inloop.inf.tu-dresden.de` to be the base directory.

### Installation steps
Note: some steps, e.g., the upstart file, are specific to Ubuntu Linux.
```bash
# Create and change to the base directory
basedir=/srv/inloop.inf.tu-dresden.de
sudo mkdir -p $basedir
sudo chown $USER:$USER $basedir
cd $basedir

# Clone the repository & change to the working copy
git clone https://github.com/st-tu-dresden/inloop.git && cd inloop

# Initialize a virtualenv that uses Python 3.x
virtualenv --python=python3 venv

# Execute setup steps specific to Ubuntu 12.04 (will invoke sudo)
./support/precise-setup.sh

# Install inloop_env wrapper
sudo ln -s $PWD/support/inloop_env /usr/local/bin

# Install requirements (inloop_env takes care of the virtualenv)
inloop_env pip install -r precise-requirements.txt

# Create a unprivileged user id which will run gunicorn
sudo adduser --system --group --home / inloop

# Create directories and ensure proper privileges:
sudo mkdir /var/run/inloop /var/log/inloop
sudo chown inloop:inloop /var/run/inloop /var/log/inloop

# Install the upstart and logrotate files
# WARNING: Don't attempt to symlink these files!
sudo cp support/upstart/*.conf /etc/init
sudo cp support/logrotate/inloop /etc/logrotate.d
```

### Configuration steps

#### Directory layout
The bundled settings module, `inloop.settings.production`, as well as the bundled
configuration snippets in the `support` directory assume the following directory
layout:

```
/srv
└── inloop.inf.tu-dresden.de/
    ├── htdocs/
    ├── inloop/
    ├── media/
    └── static/
```

If you are not fine with that, fork or branch and modify the settings module to your
needs (please refer to the Django docs for more information).

Otherwise, proceed with:

```bash
# Create the missing directories
cd $basedir
mkdir htdocs media static

# media must be writable by gunicorn/Django
sudo chown inloop:inloop media
```

#### Database init
Assuming you have a sane Postgres setup, create a database and an
associated user, then initialize the database:
```bash
# Generate a DB password and a secret key
umask 077
pwgen -s 10 1 > /tmp/password

# Create db and user
cd $basedir
./support/postgres-setup.py inloop /tmp/password inloop public | sudo -u postgres -i psql
```

Create `/etc/default/inloop`, so it exports the following environment variables:
`SECRET_KEY`, `SITE_ID`, `PG_NAME`, `PG_USER`, `PG_PASSWORD`. For instance, to
configure the database settings matching the last paragraph:

```bash
conf=/etc/default/inloop
{
  echo export PG_NAME=inloop
  echo export PG_USER=inloop
  echo export PG_PASSWORD=`cat /tmp/password`
  echo export SITE_ID=1
  echo export SECRET_KEY=`pwgen -s 60 1`
} | sudo tee $conf

# The environment file must only be readable by you and inloop,
# it contains very sensitive data!
sudo chown $USER:inloop $conf
sudo chmod 640 $conf
```

Using these settings, execute the final configuration steps:

```bash
# Load Django and INLOOP tables
cd $basedir/inloop
inloop_env ./manage.py migrate

# Create a superuser account
inloop_env ./manage.py createsuperuser

# Collect static files
inloop_env ./manage.py collectstatic
```

### Starting INLOOP

Be sure your nginx is configured to forward dynamic requests to Gunicorn.
The `support` directory contains config snippets showing how to do it.
Please refer to the nginx documentation for more information.

Using upstart, you start/reload/stop INLOOP like all other system services
using `initctl`, e.g. `initctl start inloop`. Log files to check for errors
are `/var/log/inloop/error.log` and `/var/log/upstart/inloop.log`.
