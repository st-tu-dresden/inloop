import multiprocessing

# Pidfile is useful for some management tools
pidfile = '/var/run/inloop/master.pid'

# Listen _only_ on local interface
bind = "127.0.0.1:8000"

# Baseline, can be adjusted at runtime using TTIN/TTOU
# signals to the gunicorn master
workers = multiprocessing.cpu_count() * 2 + 1
threads = 1

# Rejuvenation to prevent memory leaks
max_requests = 5000
max_requests_jitter = 500

# Access logging is done by the reverse proxy (= nginx)
accesslog = None

# Error logging
errorlog = '/var/log/inloop/error.log'
loglevel = 'info'

# FIXME: remove me later
timeout = 60
