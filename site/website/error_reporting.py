"""Bugsnag settings, switchable with the BUGSNAG_ENABLED environment variable.

Reporting is on by default when DEBUG is off (production) and off when DEBUG
is on (development). Set BUGSNAG_ENABLED=true or false to override either.
"""

BUGSNAG_MIDDLEWARE = "bugsnag.django.middleware.BugsnagMiddleware"


def bugsnag_config(*, enabled, api_key, debug, project_root):
    """The ``BUGSNAG`` setting: passed to ``bugsnag.configure``."""
    release_stage = "development" if debug else "production"
    return {
        "api_key": api_key or None,
        "project_root": project_root,
        "release_stage": release_stage,
        # Bugsnag sends nothing unless the release stage is listed here, which
        # also covers direct bugsnag.notify() calls and management commands.
        "notify_release_stages": [release_stage] if enabled else [],
        "send_environment": False,
    }


def with_bugsnag_middleware(middleware, *, enabled):
    """Put Bugsnag's middleware first when reporting is on."""
    return [BUGSNAG_MIDDLEWARE, *middleware] if enabled else list(middleware)
