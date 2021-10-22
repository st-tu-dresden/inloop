# Error and maintainance pages for INLOOP

This folder contains error pages that you can use in your nginx configuration,
such as with the following snippet inside your `server` block:

    error_page 404 /404.html;
    error_page 500 502 504 /50x.html;
    error_page 503 /offline.html;

For this to work, you must move the files in this folder (except this README)
to the document root (set by `root` directive in `nginx.conf`).

Furthermore, you should set `proxy_intercept_errors on` for the location that
contains the `proxy_pass` directive which configures the reverse proxying to
the gunicorn server as shown below.

The file `_offline.html` can be used as a starting point to implement a
maintainance page by adjusting the `/` location snippet that is given in
the [example nginx config](../etc/nginx/conf.d/inloop_example.conf) as
follows:

    location / {
        if (-f $document_root/offline.html) {
            return 503;
        }
        include includes/gunicorn_proxy_params;
        proxy_pass http://127.0.0.1:8000;
        proxy_intercept_errors on;
    }

This means: if a file `offline.html` exists in the document root, respond
with HTTP status `503` ([503 Service Unavailable][mdn-http-503]) instead of
forwarding the request to gunicorn. Nginx will serve the page configured with
the above `error_page` directives. To switch between "maintainance mode" and
"normal mode" just rename `offline.html` to `_offline.html` and vice versa.

As a bonus, you can configure a `Cache-Control` header for these responses to
prevent browsers from caching the maintainance page (they shouldn't do this, but
it doesn't hurt either). To do so, add the following location snippet to your
`server` block:

    location = /offline.html {
        internal;
        add_header Cache-Control "no-store, max-age=0" always;
    }

[mdn-http-503]: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/503
