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

**Operating system packages:** For Debian and Ubuntu, you can use

    ./support/scripts/debian_setup.sh --prod

to install all required packages.

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

Optional: separate file systems for `/var/lib/docker` and `/var/lib/inloop`

Create PostgreSQL user and schema

    sudo -u postgres -i createuser inloop
    sudo -u postgres -i createdb --owner=inloop inloop

Unix user accounts

1. Management user account `inloop` (in groups `sudo` and `docker`):

       sudo adduser inloop
       sudo adduser inloop docker
       sudo adduser inloop sudo

2. Daemon user accounts `gunicorn` and `huey`:

       sudo adduser --system --group --home /var/lib/inloop huey
       sudo adduser --system --group --home / gunicorn

SSH key w/o passphrase for `huey` (*deployment key*)

    sudo -u huey -H ssh-keygen -N ''

Prepare directories:

    sudo mkdir -p /var/lib/inloop/media/solutions
    sudo chown -R huey:huey /var/lib/inloop
    sudo chown gunicorn:gunicorn /var/lib/inloop/media/solutions


Installation
------------

Set and `export` all required [environment variables](#environment-variables).

    python3 -m venv $VENV_DIR && source $VENV_DIR/bin/activate
    pip install -r requirements/main.txt -r requirements/prod.txt
    ./manage.py migrate

    ./manage.py createsuperuser
    ./manage.py set_default_site --system-fqdn --name INLOOP

    npm install --production
    ./manage.py collectstatic
    gzip -kn $STATIC_ROOT/**/*.css $STATIC_ROOT/**/*.js

Configure automatic startup using the provided [upstart job files](../support/etc/init)
or [systemd service units](../support/etc/systemd/system).

Configure nginx by adapting the provided [example nginx location](../support/etc/nginx).


Updates
-------

    git pull
    pip install -r requirements/main.txt -r requirements/prod.txt
    ./manage.py migrate
    ./manage.py collectstatic
    sudo service gunicorn restart


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
`WEB_CONCURRENCY` | The amount of Gunicorn workers to start (`1`)
`X_ACCEL_LOCATION`| The internal `X-Accel-Redirect` location for nginx, e.g. `/sendfile`, must be set if `PROXY_ENABLED` is `True`

Additionally, the setproctitle library (which is used by Gunicorn) recognizes `SPT_NOENV`. If set,
it will [not overwrite `/proc/PID/environ`][2].

[1]: https://docs.djangoproject.com/en/stable/ref/settings/#allowed-hosts
[2]: https://pypi.python.org/pypi/setproctitle#environment-variables
