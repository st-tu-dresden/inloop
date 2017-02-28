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

**Supported operating system:** any modern Linux distribution will do the trick, but it should
be able to run Docker and Python, of course (see the [README](../README.md) for version
requirements). We recommend the latest stable release of Debian or Ubuntu LTS.

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
the server as the database administrator (`sudo -u postgres -i psql`).
