"""Gunicorn settings for api.dailyoffice2019.com: bounded concurrency.

Opt-in only. Gunicorn auto-loads ``./gunicorn.conf.py`` from its working
directory, so this file is deliberately named something else: it changes
nothing until the systemd unit passes it explicitly, e.g.

    ExecStart=/var/www/api.dailyoffice2019.com/env/bin/gunicorn \\
        -c /var/www/api.dailyoffice2019.com/deploy/gunicorn_config.py \\
        --bind <the unit's existing bind> website.wsgi:application

Command-line flags override this file, so drop any --workers/--threads/-k/
--timeout flags from the unit when adopting it. Every value below can be
overridden with an environment variable (``Environment=`` in the unit).

Why WSGI + gthread: every view is synchronous Django/DRF code. Under an ASGI
worker each in-flight request gets its own thread and its own DB connection
with no upper bound, which is how mornings ran Postgres out of connections.
Here each worker serves at most GUNICORN_THREADS requests at once; the rest
wait briefly in the listen backlog instead of opening connections.

Database connection math (see DATABASES in site/website/settings.py):

    GUNICORN_WORKERS x DB_POOL_MAX_SIZE      app connections (pool per worker)
  + cron/management commands (~2 each)       kronos jobs, migrate, shell
  + admin sessions, psql, backups
  must stay below Postgres max_connections (100 by default, 3 reserved).

Defaults: 3 workers x 10 = 30 app connections. DB_POOL_MAX_SIZE should be
>= GUNICORN_THREADS + AUDIO_BUILD_WORKERS (8 + 2) so a request never waits
on the background audio builds for a connection.

Sizing: start with WORKERS = CPU cores (``nproc``), at most 2 x cores + 1.
Raise THREADS (and DB_POOL_MAX_SIZE with it) before WORKERS: requests spend
most of their time waiting on Postgres, and each worker costs a full copy of
the app's memory. Re-check the connection math after any change.

To keep an ASGI worker instead, use ``-k website.uvicorn_worker.BoundedUvicornWorker
website.asgi:application``; it caps in-flight requests per worker at
UVICORN_LIMIT_CONCURRENCY (answering 503 beyond it).
"""

import os


def _int(name, default):
    return int(os.environ.get(name, default))


# Only used when the command line names no application.
wsgi_app = "website.wsgi:application"
chdir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "site")

workers = _int("GUNICORN_WORKERS", 3)
worker_class = os.environ.get("GUNICORN_WORKER_CLASS", "gthread")
threads = _int("GUNICORN_THREADS", 8)

# Worker heartbeat timeout (a stuck sync worker is restarted after this). With
# gthread it does not cap a single slow request; audio generation is no
# longer done inside requests (site/office/audio_builds.py), so none should be
# long.
timeout = _int("GUNICORN_TIMEOUT", 60)
graceful_timeout = _int("GUNICORN_GRACEFUL_TIMEOUT", 30)
keepalive = _int("GUNICORN_KEEPALIVE", 5)

# Off by default: recycling a worker also stops its background audio builds
# (clients simply retry). Set e.g. 2000 if worker memory grows over time.
max_requests = _int("GUNICORN_MAX_REQUESTS", 0)
max_requests_jitter = _int("GUNICORN_MAX_REQUESTS_JITTER", 200)

# Load the app in each worker after fork, so no DB pool or memcached socket is
# ever shared between processes.
preload_app = False

accesslog = os.environ.get("GUNICORN_ACCESS_LOG") or None
errorlog = os.environ.get("GUNICORN_ERROR_LOG", "-")
