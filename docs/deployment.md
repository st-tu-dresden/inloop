Deployment Manual
=================

**Warning**:
Setting up and operating INLOOP in a production environment requires a solid understanding of
Linux server administration and familiarity with PostgreSQL, Redis and nginx.


Overview
--------

Although INLOOP is a Python application, it cannot simply be installed using `pip install`.
Instead, we use a Git based deployment and perform a checkout of the latest stable code from the
`master` branch.

INLOOP is a divided into several components and depends on multiple third-party components. Each
one will run as a separate operating system process. The following diagram shows their
responsibilities and interactions:

![INLOOP architecture](figures/architecture.png)

Things to note:

- The core components of INLOOP, the web application and the job queue (the blue boxes), are both
  written in Python and communicate with each other via Redis and the PostgreSQL database. The
  former one is used as session store and job broker, the latter one for general persistence.
- Client HTTP(S) requests are first buffered and proxied by nginx, a robust, small and fast
  webserver which, among other advantages, does a better job at handling SSL/TLS encryption and
  serving static files than Gunicorn/Python.
- The reverse proxy is the only component that is accessible from the "outside" (*the internet*).
  All other components communicate via the local loopback interface or a private network.
- For development purposes, Django's `runserver` command incorporates everything that nginx,
  Gunicorn and PostgreSQL provide in production (the green area).
- In fact, INLOOP is a distributed application: it is possible to run the huey queue and Docker
  runtime on another host. For this to work, one needs to setup a shared filesystem (e.g., NFS).


Prerequisites
-------------

**Supported operating system:** This manual is written for Debian 8+ and Ubuntu 16.04+. Any
other modern Linux distribution should also do the trick, given that it is able to run Docker and
Python (see the [README](../README.md) for exact version requirements).

**Docker setup**: see the [installation notes](installation_notes.md).

**Hostname setup:** verify that your system's hostname is configured correctly. `hostname` and
`hostname -f` should print the short and fully qualified hostname of your machine, e.g.:

    $ hostname
    inloop
    $ hostname -f
    inloop.inf.tu-dresden.de

**SSL/TLS key and certificate:** INLOOP relies on HTTPS to safely handle user authentication and
protect sensitive user data in transit. For evaluation purposes or a staging site, a self-signed
certificate will be enough. For a production deployment, a certificate signed by a browser-accepted
CA, such as [Let's Encrypt](https://letsencrypt.org), is needed.

**Postgres up and running**: ensure that the PostgreSQL server is running and you can connect to
the server using the database administrator role (`postgres`):

    $ sudo -u postgres -i psql -c '\l'
                                      List of databases
       Name    |  Owner   | Encoding |   Collate   |    Ctype    |   Access privileges
    -----------+----------+----------+-------------+-------------+-----------------------
     postgres  | postgres | UTF8     | en_US.UTF-8 | en_US.UTF-8 |
     template0 | postgres | UTF8     | en_US.UTF-8 | en_US.UTF-8 | =c/postgres          +
               |          |          |             |             | postgres=CTc/postgres
     template1 | postgres | UTF8     | en_US.UTF-8 | en_US.UTF-8 | postgres=CTc/postgres
    (3 rows)


Preparations
------------

#### Optional: isolate file systems

For increased robustness, we recommend to create a separate partition (or LVM volume) and file
system for the Docker runtime (`/var/lib/docker`) and the INLOOP data folder (`/var/lib/inloop`).
The data folder may be mounted with stricter mount options (`nosuid` and `nodev`). How to do this
is out of scope of this manual.


#### Unix user accounts

As mentioned in the [overview](#overview), the core components of INLOOP run under separate,
unprivileged daemon user accounts, `gunicorn` and `huey`, created with:

    sudo adduser --system --group --home /var/lib/inloop huey
    sudo adduser --system --group --home / gunicorn

Furthermore, a privileged management user account `inloop` must be created with:

    sudo adduser inloop
    sudo adduser inloop docker
    sudo adduser inloop sudo

The `inloop` account will be used by you for Git checkouts/pulls and the execution of Django
management commands.


#### SSH deployment key for imports from Git

The Git import runs non-interactively and there will be no password prompt. Importing from a public
Git repository works out of the box, but for protected repositories, a SSH key without a passphrase
must be generated for the unix user `huey`:

    sudo -u huey -H ssh-keygen -N ''

This key can then be used as a *deployment key* for GitHub.


#### PostgreSQL user and database

Create a PostgreSQL user and database, both named `inloop`:

    sudo -u postgres -i createuser inloop
    sudo -u postgres -i createdb --owner=inloop inloop

Because we have chosen the same name for the PostgreSQL user, the unix user `inloop` is now able to
use `psql` without further authentication. This comes in handy for management tasks, such as the
creation of database backups.


#### Prepare directories

We will place `MEDIA_ROOT` (see below) into `huey`'s home directory: `/var/lib/inloop/media`. For
the user uploads to work, `gunicorn` must be able to write to `<MEDIA_ROOT>/solutions`. Everything
else must be owned by `huey`:

    sudo mkdir -p /var/lib/inloop/media/solutions
    sudo chown -R huey:huey /var/lib/inloop
    sudo chown gunicorn:gunicorn /var/lib/inloop/media/solutions


Installation
------------

1. Log into the `inloop` user account, either via `su - inloop` or `sudo -u inloop -i`.
2. Clone the INLOOP Git repository into `inloop`'s home:

        git clone https://github.com/st-tu-dresden/inloop.git ~/inloop
        cd ~/inloop

3. Install required operating system packages (for Debian and Ubuntu):

        ./support/scripts/debian_setup.sh --prod

4. Create a clean virtualenv for INLOOP:

        python3 -m venv ~/virtualenv

5. Configure INLOOP through environment variables. We will use the `envdir` tool from djb's
   daemontools package for this purpose, because it makes it very easy to manage a set of
   environment variables through files:

        mkdir ~/envdir
        chmod 700 ~/envdir

   For each [required environment variable](#environment-variables), a file has to be created:

        echo VALUE > ~/envdir/VARIABLE_NAME

   For example:

        echo inloop.settings > ~/envdir/DJANGO_SETTINGS_MODULE
        echo en_US.UTF-8 > ~/envdir/LANG
        echo ~/inloop > ~/envdir/PYTHONPATH
        echo ~/virtualenv/bin:/usr/bin:/bin > ~/envdir/PATH
        echo ~/htdocs/static > ~/envdir/STATIC_ROOT
        echo /var/lib/inloop/media > ~/envdir/MEDIA_ROOT
        pwgen -s 64 1 > ~/envdir/SECRET_KEY
        ...

   Since the services run under different unix user accounts, a password must be set for the
   `inloop` database user:

        psql -c "ALTER ROLE inloop WITH PASSWORD '<password>';"

   Be sure to use the same password in the `DATABASE_URL` environment variable:

        echo postgres://inloop:<password>@localhost:5432/inloop > ~/envdir/DATABASE_URL

   A fully populated envdir will look like this:

        inloop@inloop:~$ tree ~/envdir
        /home/inloop/envdir/
        ├── ADMINS
        ├── ALLOWED_HOSTS
        ├── CACHE_URL
        ├── DATABASE_URL
        ├── DJANGO_SETTINGS_MODULE
        ├── FROM_EMAIL
        ├── GITHUB_SECRET
        ├── GIT_ROOT
        ├── LANG
        ├── MEDIA_ROOT
        ├── PATH
        ├── PROXY_ENABLED
        ├── PYTHONPATH
        ├── REDIS_URL
        ├── SECRET_KEY
        ├── SPT_NOENV
        ├── STATIC_ROOT
        ├── WEB_CONCURRENCY
        └── X_ACCEL_LOCATION

        0 directories, 19 files

    You can list the effective configuration using:

        envdir ~/envdir env

6. Load the environment:

        exec envdir ~/envdir $SHELL

   Append the above line to `~/.bash_profile`, to automagically load the envdir whenever you login
   as user `inloop`.

7. Install all Python requirements and run database migrations. Before, please verify that the
   output of `command -v pip` is `/home/inloop/virtualenv/bin/pip` and rerun steps 4-6 if this
   is not the case.

        cd ~/inloop
        pip install -r requirements/main.txt -r requirements/prod.txt
        django-admin migrate

   **Tip**: perform a PostgreSQL backup before migrating with `pg_dump -Fc -f ~/inloop.pgdump`.

8. Install third-party JS/CSS frameworks and collect all static files into `STATIC_ROOT`:

        npm install --production
        mkdir -p $STATIC_ROOT
        django-admin collectstatic

9. Create a superuser, load initial data and configure Django's contrib.sites app:

        django-admin createsuperuser
        django-admin loaddata about_pages staff_group
        django-admin set_default_site --system-fqdn --name INLOOP

10. Finally, install the provided [upstart job files](../support/etc/init) or [systemd service
    units](../support/etc/systemd/system) to their appropriate places. For `systemd` systems:

        sudo cp ~/inloop/support/etc/systemd/system/*.service /etc/systemd/system
        sudo systemctl enable gunicorn.service huey.service

    For `upstart` systems:

        sudo cp ~/inloop/support/etc/init/*.conf /etc/init

11. Configure nginx as a reverse proxy by copying and adapting the provided [example nginx
   location](../support/etc/nginx) to `/etc/nginx/conf.d` (or `/etc/nginx/sites-available.d`).

Gunicorn and huey may be started and stopped via `sudo service [start|stop|restart] <name>` and
will start automatically at boot.


Updates
-------

1. Load the latest code from the INLOOP `master` branch:

        cd ~/inloop
        git pull

2. Repeat steps 7 and 8 from the [installation chapter](#installation).

3. Restart services:

        sudo service gunicorn restart

   Huey will be restarted automatically as a dependent service.


Troubleshooting
---------------

Got a server error? Look here for hints:

* Check your mailbox, because Django sends detailed error reports via e-mail.
* Look for error messages in the nginx error log, usually located in `/var/log/nginx/error.log`.
* For `systemd` users, service logs for gunicorn and huey can be viewed using

       sudo journalctl _SYSTEMD_UNIT=gunicorn.service

  and

       sudo journalctl _SYSTEMD_UNIT=huey.service

* If you are still stuck with `upstart` instead of `systemd`, the service logs are written to
   `/var/log/upstart/gunicorn.log` and `/var/log/upstart/huey.log`.

The most common source of errors are wrong file system permissions. Please double check that you
have changed ownership and access rights as described in the [preparation section](#preparations).


Environment variables
---------------------

The following variables are **required**:

Name                      | Description
------------------------- | -----------
`ADMINS`                  | Comma-separated list of email addresses which receive error reports
`ALLOWED_HOSTS`           | Comma-separated list of [allowed hosts][1]
`CACHE_URL`               | 12factor style cache URL, e.g. `redis://localhost:1234/0`
`DATABASE_URL`            | 12factor style database URL, e.g. `postgres://user:pass@host:port/db`
`DJANGO_SETTINGS_MODULE`  | Set to `inloop.settings` unless you know what you are doing
`FROM_EMAIL`              | Address used for outgoing mail, e.g. `inloop@example.com`
`GITHUB_SECRET`           | Github webhook endpoint secret
`GIT_ROOT`                | Must be a subdirectory of `MEDIA_ROOT`
`LANG`                    | Set to `en_US.UTF-8` unless you know what you are doing
`MEDIA_ROOT`              | Path to the directory for user uploads
`PYTHONPATH`              | Set it to the path of the INLOOP git clone
`REDIS_URL`               | Redis URL used for the queue, e.g. `redis://localhost:1234/1`
`SECRET_KEY`              | Set to a long **random** string
`STATIC_ROOT`             | Path to the directory where all static files are collected


The following variables may be set **optionally**:

Name              | Description (default value)
----------------- | ---------------------------
`DEBUG`           | Debug mode, don't use this in production (`False`)
`EMAIL_URL`       | 12factor style email URL (`smtp://:@localhost:25`)
`INTERNAL_IPS`    | Comma-separated list of IP addresses for which more verbose error reports are shown
`PROXY_ENABLED`   | Must be set to `True` if running behind nginx (`False`)
`SECURE_COOKIES`  | Enable SSL/TLS protection for session and CSRF cookies (`True`)
`TIME_ZONE`       | The time zone used for displayed dates (`Europe/Berlin`)
`WEB_CONCURRENCY` | The amount of Gunicorn workers to start (`1`)
`X_ACCEL_LOCATION`| The internal `X-Accel-Redirect` location for nginx, e.g. `/sendfile`, must be set if `PROXY_ENABLED` is `True`

Additionally, the setproctitle library (which is used by Gunicorn) recognizes `SPT_NOENV`. If set,
it will [not overwrite `/proc/PID/environ`][2].

[1]: https://docs.djangoproject.com/en/stable/ref/settings/#allowed-hosts
[2]: https://pypi.python.org/pypi/setproctitle#environment-variables
