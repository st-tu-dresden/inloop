from multiprocessing import cpu_count
from os import environ

# listen _only_ on local interface
bind = ["127.0.0.1:8000"]

# can also be adjusted at runtime using TTIN/TTOU signals
workers = int(environ.get("WEB_CONCURRENCY", cpu_count() * 2))
threads = 1

# rejuvenation to prevent memory leaks
max_requests = 500
max_requests_jitter = 100

# access logging is done by the reverse proxy
accesslog = None

# log errors to stdout, which is recorded by systemd journal
errorlog = "-"
loglevel = "info"
