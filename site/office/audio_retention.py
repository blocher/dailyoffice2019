"""Which generated audio files are permanent.

Most office audio is a cache: combined tracks and clips can be deleted and are
rebuilt on the next request. Podcast episodes are different. Once an episode
is in a public feed, podcast apps keep pointing at its enclosure URL forever,
so its file must never be removed by a cleanup or audit command.

Episodes live under ``MEDIA_ROOT/podcasts/`` (see ``podcasts.storage``). Every
command that deletes media files checks ``is_permanent`` first.
"""

import os

from django.conf import settings

PODCAST_MEDIA_SUBDIR = "podcasts"


def podcast_media_root():
    return os.path.join(settings.MEDIA_ROOT, PODCAST_MEDIA_SUBDIR)


def is_permanent(path):
    """True when ``path`` is (or is inside) the permanent podcast archive."""
    root = os.path.realpath(podcast_media_root())
    target = os.path.realpath(path)
    return target == root or target.startswith(root + os.sep)
