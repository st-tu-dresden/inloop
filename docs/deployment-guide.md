## Deployment HOWTO

This document describes the steps needed for a production setup of INLOOP on
Ubuntu 12.04. It should work out-of-the-box for any Debian-based Linux that
uses upstart as its init system.


### Overview

The setup follows current best practices and builds upon the following
components:

* Nginx, acting as a reverse proxy. This is the only service accessible
  from outside. It terminates HTTP and HTTPS connections, handles serving
  static files and routes dynamic requests to the backend.
* Gunicorn, a Python-based application server running the Django application.
* PostgreSQL, an awesome SQL database server.
* Redis, a fast persistent key-value store.

Why? The Django built-in server and SQLite are of course sufficient during
development. But they are not designed for larger scale and/or production
use. Using the mentioned components offers several advantages, among others
improved security through separation/isolation (each component runs in its
own process with its own user id).


### Before installing

**NOTE**: if you are testing this on the Vagrant box just use

    sudo python3.4 /vagrant/setup_tools/provision.py /srv/apps
    su - inloop

and proceed with [Installation steps](#installation-steps).

Please ensure that you have installed all packages that are defined in the
`Vagrantfile`. Especially, make sure you have Python 3.4!

Next, use the provisioning script to setup the recommended deployment
structure with `/srv/apps` as the base directory:

    scp setup_tools/provision.py user@your_host
    ssh user@your_host
    sudo python3 provision.py /srv/apps

When called with `/srv/apps`, it will set up:

- two users (`inloop` for developers/admins, `inloop-run` for the daemons), each
  having their home directory under `/srv/apps`,
- passwordless SSH deploy keys for both users for read-only access to protected
  GitHub repositories,
- the ability for `inloop` to become `inloop-run` without a password

To make the `inloop` account a little bit more usable, you can opt to give it a
password (`sudo passwd inloop`) and enable password-authenticated sudo (with
`sudo usermod -aG sudo inloop`). Add your (and other developers') public SSH keys
to `.ssh/authorized_keys` if you want.

The bundled `nginx` config requires SSL certificates to be installed for your
`server_name` (see `local_conf.py`).


### Installation steps

For a fresh install:

1. Login as `inloop`. You should be automatically running in a virtualenv. If not,
   you have failed to follow the steps in the last section :(
2. Clone the INLOOP repo with `git clone <inloop-repo-url> inloop`.
3. Change to the clone with `cd inloop` and *keep it like this for the next steps*.
4. Create the local config with `python setup_tools/make_conf.py > local_conf.py`.
   Review and edit `local_conf.py` as necessary.
5. Install the support files to `/etc` with `sudo python3 setup_tools/install.py`.
6. Initialize PostgreSQL with `python3 setup_tools/pq_init.py | sudo -u postgres -i psql`.
   Try `psql --list` to see if that worked.
7. Reload nginx with `sudo service nginx reload`.
8. Initialize and load the application with `python deploy.py`. This can take a while.

Updates are easy: `git pull && python deploy.py`. Service reloading is handled by
the deploy tool, but you can do it manually with `sudo service inloop-web restart`
(this also restarts `inloop-queue`).

The deploy tool also saves DB dumps in `~/db_snapshots` before applying migrations.


### Debugging

Check the log files:

- `/var/log/nginx/*`
- `/var/log/inloop/error.log`
- `/var/log/upstart/inloop-*.log`
