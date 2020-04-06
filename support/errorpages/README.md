# Error and maintainance pages for INLOOP

This folder contains error pages that you can use in your nginx configuration,
such as with the following snippet inside your `server` block:

    error_page 404 /404.html;
    error_page 500 502 503 503 /50x.html;

For this to work, you must move the files in this folder (except this README)
to the document root (set by `root` directive in `nginx.conf`).

Furthermore, you should set `proxy_intercept_errors on` for the location that
contains the `proxy_pass` directive which configures the reverse proxying to
the gunicorn server as shown below.

The file `_offline.html` can be used as a starting point to implement a
maintaince page using the `try_files` directive:

    location / {
        try_files /offline.html @gunicorn;
    }

This means: if a file `offline.html` exists, show this one instead of
forwarding the request to gunicorn. To switch between "maintainance mode" and
"normal mode" just rename `offline.html` to `_offline.html` and vice versa.

This assumes you use a named location `@gunicorn`, such as:

    location @gunicorn {
        include includes/gunicorn_proxy_params;
        proxy_pass http://127.0.0.1:8000;
        proxy_intercept_errors on;
    }
