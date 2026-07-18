from django.conf import settings

PIPELINE_LEGACY = "legacy"
PIPELINE_V2 = "v2"
PIPELINE_GEMINI = "gemini"
VALID_PIPELINES = {PIPELINE_LEGACY, PIPELINE_V2, PIPELINE_GEMINI}

_override_pipeline = None


def get_audio_pipeline():
    if _override_pipeline in VALID_PIPELINES:
        return _override_pipeline
    value = getattr(settings, "OFFICE_AUDIO_PIPELINE", PIPELINE_V2)
    value = str(value or PIPELINE_V2).strip().lower()
    if value not in VALID_PIPELINES:
        return PIPELINE_V2
    return value


def set_audio_pipeline(pipeline):
    """Temporarily override pipeline (management commands / tests). Pass None to clear."""
    global _override_pipeline
    if pipeline is None:
        _override_pipeline = None
        return
    value = str(pipeline).strip().lower()
    if value not in VALID_PIPELINES:
        raise ValueError(f"Invalid audio pipeline: {pipeline}")
    _override_pipeline = value
