"""Build on-demand office audio outside the web request.

A web request for ``include_audio_links`` renders the office with generation
*deferred*: every point that would call a TTS provider or ffmpeg raises
``AudioNotReady`` instead. The view then schedules one background build for
that exact URL and answers ``202 Preparing`` at once, and the client polls
until the build has finished. A request therefore never holds a database
connection (or an app-server thread) for the seconds-to-minutes a build takes.

Builds run in a small per-process thread pool (``AUDIO_BUILD_WORKERS``). A
cache lock (memcached in production, so shared by all workers) keeps the same
URL from being built twice at once; per-clip file locks in the serializer stop
two different URLs from paying for the same clip. A build that dies with its
worker (deploys restart the app) simply leaves the client to retry; deploys
also flush memcached, so no stale lock survives them.

Trusted in-process callers (the ``update_audio_files`` cron and the Gemini
batch planner) never defer: the context variable defaults to "generate".
"""

import hashlib
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from contextvars import ContextVar

from django.conf import settings
from django.core.cache import cache
from django.db import connections

logger = logging.getLogger(__name__)

GENERATION_DEFERRED = ContextVar("audio_generation_deferred", default=False)
# Within deferred generation, whether the combined track may still be
# assembled (ffmpeg concat of clips that all exist). Only a custom podcast's
# episode request allows it (see podcasts.custom); speech is never synthesized.
ASSEMBLY_ALLOWED = ContextVar("audio_assembly_allowed", default=False)


class AudioNotReady(Exception):
    """Audio would have to be synthesized or assembled; not inside a request."""


def generation_deferred():
    return GENERATION_DEFERRED.get()


def ensure_generation_allowed():
    """Call at every point that would reach a TTS provider or run ffmpeg."""
    if GENERATION_DEFERRED.get():
        raise AudioNotReady()


def ensure_assembly_allowed():
    """Call before concatenating existing clips into a combined track."""
    if GENERATION_DEFERRED.get() and not ASSEMBLY_ALLOWED.get():
        raise AudioNotReady()


@contextmanager
def deferred_generation(allow_assembly=False):
    token = GENERATION_DEFERRED.set(True)
    assembly = ASSEMBLY_ALLOWED.set(allow_assembly)
    try:
        yield
    finally:
        ASSEMBLY_ALLOWED.reset(assembly)
        GENERATION_DEFERRED.reset(token)


def release_db_connections():
    """Hand this thread's database connections back before slow external work.

    With the connection pool this is cheap: the next query checks a connection
    out again. Never closes a connection inside a transaction.
    """
    for connection in connections.all(initialized_only=True):
        if not connection.in_atomic_block:
            connection.close()


def _key(prefix, identity):
    return f"office-audio-build:{prefix}:{hashlib.sha256(identity.encode()).hexdigest()}"


def _cached(key):
    try:
        return cache.get(key) is not None
    except Exception:
        logger.warning("Audio build status unavailable", exc_info=True)
        return False


def is_building(identity):
    return _cached(_key("lock", identity))


def has_failed(identity):
    return _cached(_key("failed", identity))


def _acquire(lock_key):
    """cache.add is atomic in memcached, so only one process wins the lock."""
    try:
        return cache.add(lock_key, 1, timeout=settings.AUDIO_BUILD_LOCK_SECONDS)
    except Exception:
        # Cache outage: fall back to this process's own de-duplication.
        logger.warning("Audio build lock unavailable", exc_info=True)
        return True


_executor = None
_pending = set()
_lock = threading.Lock()


def _get_executor():
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(
            max_workers=max(1, settings.AUDIO_BUILD_WORKERS), thread_name_prefix="office-audio-build"
        )
    return _executor


def pending_count():
    """Builds queued or running in this process."""
    with _lock:
        return len(_pending)


def schedule(identity, build):
    """Run ``build()`` in the background unless this identity is already queued.

    ``build`` returns True on success. Returns True when a build was queued.
    """
    lock_key = _key("lock", identity)
    with _lock:
        if identity in _pending or len(_pending) >= settings.AUDIO_BUILD_MAX_PENDING:
            return False
        if not _acquire(lock_key):
            return False
        _pending.add(identity)
        executor = _get_executor()
    try:
        executor.submit(_run, identity, build)
    except Exception:
        _finish(identity)
        raise
    return True


def _finish(identity):
    with _lock:
        _pending.discard(identity)
    try:
        cache.delete(_key("lock", identity))
    except Exception:
        logger.warning("Audio build lock release failed", exc_info=True)


def _run(identity, build):
    succeeded = False
    try:
        succeeded = bool(build())
    except Exception:
        logger.exception("Background office audio build failed")
    finally:
        try:
            if succeeded:
                cache.delete(_key("failed", identity))
            else:
                cache.set(_key("failed", identity), 1, timeout=settings.AUDIO_BUILD_FAILURE_SECONDS)
        except Exception:
            logger.warning("Audio build status update failed", exc_info=True)
        finally:
            _finish(identity)
            # Threads outside the request cycle never get request_finished, so
            # return the pooled connection here or the pool slowly drains.
            release_db_connections()
    return succeeded
