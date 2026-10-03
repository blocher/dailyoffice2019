#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "website.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    # Management commands do not construct Django's Bugsnag middleware.
    # Initialize the same notifier before running them (including cron jobs).
    import bugsnag
    from django.conf import settings

    bugsnag.configure(**settings.BUGSNAG)
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
