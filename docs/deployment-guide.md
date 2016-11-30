## Deployment guide

**Note**: This document is not 100% complete and still being worked on.

### Overview

INLOOP is a standard Django project and as such, the [official Django
deployment docs][1] apply.

This document outlines the recommended approach of running INLOOP on
Gunicorn behind NGINX configured as a TLS-terminating reverse proxy.


### Twelve factor style configuration

INLOOP settings are completely controlled with environment variables.

##### Required envvars

Name                        | Description
--------------------------- | -------------
`ALLOWED_HOSTS`             | Comma-separated list of [allowed hosts][2]
`CACHE_URL`                 | 12factor style cache URL, e.g. `redis://localhost:1234/0`
`DATABASE_URL`              | 12factor style database URL, e.g. `postgres://user:pass@host:port/db`
`DJANGO_SETTINGS_MODULE`    | Set to `inloop.settings` unless you know what you are doing
`FROM_EMAIL`                | Address used for outgoing mail, e.g. `inloop@example.com`
`GITHUB_SECRET`             | Github webhook endpoint secret
`LANG`                      | Set to `en_US.UTF-8` unless you know what you are doing
`REDIS_URL`                 | Redis URL used for the queue, e.g. `redis://localhost:1234/1`
`SECRET_KEY`                | Set to a long random string


*TBD: list optional variables, too.*


### Installation

1. Ensure you've installed all requirements mentioned in the [README]
   (../README.md).

2. Additionally run `pip install -r requirements/prod.txt` in your virtualenv.

3. Set and `export` all required [environment variables](#required-envvars).

4. Unless you are using SQLite, you have to create the user and database you
   specified in `DATABASE_URL` using `createdb`/`createuser` (PostgreSQL) or
   `mysqladmin` (MySQL/MariaDB).

4. Run `./manage.py migrate` and `./manage.py createsuperuser`.


### Startup

The following jobs must be run using a process manager such as `systemd` or
`supervisord`:

* **web app**: `gunicorn --workers=5 inloop.wsgi:application`
* **task queue**: `python manage.py run_huey --workers=2`

Be sure to run each job under a unique, job-specific uid with the least
privileges possible. The **task queue** needs to be able to speak to the docker
daemon and should run in the supplementary `docker` group.

We plan to ship suitable `systemd` service units as part of INLOOP very soon.


#### Docker cgroup limits

*TBD: DoS mitigation with cgroup cpu.shares etc.*


### NGINX configuration

NGINX needs to be configured as follows:

1. Terminate TLS connections and redirect plain text HTTP to HTTPS.

2. All requests must be proxied to Gunicorn `127.0.0.1:8000`.

3. The proxy (and **only** the proxy) must set the following request headers:
   `X-Forwarded-Host`, `X-Forwarded-Port` and `X-Forwarded-Proto`.

4. The proxy should set response headers as outlined in the [Django security
   middleware docs][3].


[1]: https://docs.djangoproject.com/en/stable/howto/deployment/
[2]: https://docs.djangoproject.com/en/stable/ref/settings/#allowed-hosts
[3]: https://docs.djangoproject.com/en/stable/ref/middleware/#module-django.middleware.security
