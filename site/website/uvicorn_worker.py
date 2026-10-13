"""Gunicorn's Uvicorn worker with a cap on in-flight requests.

Under ASGI, Django runs each synchronous view in its own thread with its own
database connection, so an unbounded worker can open as many connections as
there are concurrent requests. ``limit_concurrency`` makes Uvicorn answer 503
beyond the cap instead. Prefer the WSGI gthread setup in
deploy/gunicorn_config.py; use this only if the app must stay on ASGI:

    gunicorn -c deploy/gunicorn_config.py \\
        -k website.uvicorn_worker.BoundedUvicornWorker website.asgi:application
"""

import os

try:
    from uvicorn_worker import UvicornWorker
except ImportError:  # The worker moved out of uvicorn; older releases still ship it.
    from uvicorn.workers import UvicornWorker


class BoundedUvicornWorker(UvicornWorker):
    CONFIG_KWARGS = {
        **UvicornWorker.CONFIG_KWARGS,
        # Counts open connections as well as requests, so leave headroom for
        # keep-alive connections from the proxy.
        "limit_concurrency": int(os.environ.get("UVICORN_LIMIT_CONCURRENCY", 32)),
    }
