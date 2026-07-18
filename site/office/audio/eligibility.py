from dataclasses import dataclass

ENGLISH_DISPLAY_LANGUAGES = {"english"}
ENGLISH_LANGUAGE_STYLES = {"contemporary", "traditional"}
ENGLISH_PSALM_TRANSLATIONS = {"contemporary", "traditional"}
SUPPORTED_BIBLE_TRANSLATIONS = {"esv", "kjv"}

UNAVAILABLE_MESSAGES = {
    "bible_translation": (
        "Audio is only available when the Bible translation is the English Standard Version (ESV) "
        "or the King James Version (KJV). Support for other translations and languages is still in progress."
    ),
    "display_language": (
        "Audio is only available for English offices (contemporary or traditional). "
        "Support for other languages is still in progress."
    ),
    "language_style": (
        "Audio is only available for English contemporary or traditional language settings. "
        "Support for other languages is still in progress."
    ),
    "psalm_translation": (
        "Audio is only available when the psalm translation is English contemporary or traditional. "
        "Support for other languages is still in progress."
    ),
}


@dataclass(frozen=True)
class AudioEligibility:
    available: bool
    reason: str | None = None
    message: str | None = None


def _setting_value(settings_obj, key, default=""):
    if settings_obj is None:
        return default
    if hasattr(settings_obj, "get"):
        value = settings_obj.get(key, default)
    else:
        value = getattr(settings_obj, key, default)
    if value is None:
        return default
    return str(value).strip().lower()


def check_audio_eligibility(settings_obj) -> AudioEligibility:
    """Audio is English contemporary/traditional liturgy with ESV or KJV only."""
    display_language = _setting_value(settings_obj, "display_language", "english") or "english"
    language_style = _setting_value(settings_obj, "language_style", "contemporary")
    psalm_translation = _setting_value(settings_obj, "psalm_translation", "contemporary")
    bible_translation = _setting_value(settings_obj, "bible_translation", "esv")

    if display_language not in ENGLISH_DISPLAY_LANGUAGES:
        return AudioEligibility(False, "display_language", UNAVAILABLE_MESSAGES["display_language"])
    if language_style not in ENGLISH_LANGUAGE_STYLES:
        return AudioEligibility(False, "language_style", UNAVAILABLE_MESSAGES["language_style"])
    if psalm_translation not in ENGLISH_PSALM_TRANSLATIONS:
        return AudioEligibility(False, "psalm_translation", UNAVAILABLE_MESSAGES["psalm_translation"])
    if bible_translation not in SUPPORTED_BIBLE_TRANSLATIONS:
        return AudioEligibility(False, "bible_translation", UNAVAILABLE_MESSAGES["bible_translation"])
    return AudioEligibility(True)
