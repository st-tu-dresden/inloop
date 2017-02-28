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

**Supported operating system:** This manual is written for Debian 8 and Ubuntu 16.04/14.04. Any
other modern Linux distribution should also do the trick, given that it is able to run Docker and
Python (see the [README](../README.md) for exact version requirements).

**Operating system packages:** ensure you've installed all dependencies listed in the
[README](../README.md).

**Hostname setup:** verify your system's hostname is setup correctly. `hostname` and `hostname -f`
should print the short and fully qualified hostname of your machine, e.g.:

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


Environment variables
---------------------

The following variables are **required**:

Name                      | Description
------------------------- | -----------
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
`EMAIL_URL`       | 12factor style email URL (`smtp://:@localhost:25`)
`SECURE_COOKIES`  | Enable SSL/TLS protection for session and CSRF cookies (`true`)
`WEB_CONCURRENCY` | The amount of Gunicorn workers to start (`1`)

Additionally, the setproctitle library (which is used by Gunicorn) recognizes `SPT_NOENV`. If set,
it will [not overwrite `/proc/PID/environ`][2].

[1]: https://docs.djangoproject.com/en/stable/ref/settings/#allowed-hosts
[2]: https://pypi.python.org/pypi/setproctitle#environment-variables
