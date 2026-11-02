"""Account for every paid text-to-speech request, and report audio paid for twice.

Generated audio is cached forever (adding disk is cheap; synthesizing again is
not). Two signs that already-paid audio is being bought again are reported to
Bugsnag as they happen:

* a clip is synthesized although its cache record survives: an ``AudioClip``
  row or word-timing sidecar for a single clip, or the timing sidecar of a
  dialogue clip. Deliberate rebuilds (the admin actions, ``rebuild_audio_clip``)
  delete the record with the file, so they are not reported;
* a request is retried after a timeout or a dropped connection, when the
  provider may already have charged for the audio it never delivered.

Each paid request is recorded as a ``TTSGeneration`` so ``check_tts_spend`` can
compare our own count with the provider's bill every day and catch causes
nobody has thought of yet.
"""

import logging

import bugsnag

logger = logging.getLogger(__name__)


class AudioRegenerated(Exception):
    """Audio that was already generated (and paid for) is being generated again."""


class PossiblyChargedRetry(Exception):
    """A provider request is being retried after a failure that may have been billed."""


def _notify(exc, context, metadata):
    try:
        bugsnag.notify(exc, severity="warning", context=context, metadata={"audio": metadata})
    except Exception:
        logger.exception("Bugsnag notification failed for %s", context)


def submitted_characters(provider, text):
    """Characters the provider bills for ``text``, including any cue it adds."""
    prepare = getattr(provider, "prepare_text", None)
    try:
        return len(prepare(text)[0]) if prepare else len(text)
    except Exception:
        return len(text)


def report_regeneration(provider, kind, key, reason):
    logger.warning("Regenerating cached %s audio %s (%s): %s", provider, kind, key, reason)
    _notify(
        AudioRegenerated(f"Cached {kind} audio is being generated again"),
        "audio_regeneration",
        {"provider": provider, "kind": kind, "key": key, "reason": reason},
    )


def report_retry(provider, attempt, error):
    """Report a retry after an exception; status-code retries (429, 5xx) are not billed."""
    logger.warning("%s request retried after %s (attempt %d); it may have been billed", provider, error, attempt)
    _notify(
        PossiblyChargedRetry(f"{provider} request retried after {type(error).__name__}"),
        "audio_retry",
        {"provider": provider, "attempt": attempt, "error": type(error).__name__},
    )


def paid_before(key):
    """Whether a generation of ``key`` was recorded, even if its audio was never kept."""
    from office.models import TTSGeneration

    try:
        return TTSGeneration.objects.filter(key=key).exists()
    except Exception:
        # Accounting must never block audio that is needed now.
        logger.exception("Could not look up earlier generations")
        return False


def record_generation(provider, kind, key, characters, regenerated=False):
    from office.models import TTSGeneration

    try:
        TTSGeneration.objects.create(
            provider=provider, kind=kind, key=key, characters=characters, regenerated=regenerated
        )
    except Exception:
        # Accounting must never cost the audio that was just paid for.
        logger.exception("Could not record a %s generation", provider)
