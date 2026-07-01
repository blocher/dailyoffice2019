import re
from dataclasses import dataclass

DEFAULT_CONTEXT_CHARS = 50

# Allowed characters immediately before/after a CE/BCE year marker.
BOUNDARY_CHARS = set(" \t\n\r.,;:!?\"'()[]{}")

BCE_TOKEN = re.compile(r"B(?:\.\s*)?C(?:\.\s*)?E\.?", re.IGNORECASE)
CE_TOKEN = re.compile(r"C(?:\.\s*)?E\.?", re.IGNORECASE)


@dataclass(frozen=True)
class TextReplacement:
    original: str
    replacement: str
    context_before: str
    context_after: str


def _has_valid_start_boundary(text: str, start: int) -> bool:
    if start == 0:
        return True
    return text[start - 1] in BOUNDARY_CHARS


def _has_valid_end_boundary(text: str, end: int) -> bool:
    if end == len(text):
        return True
    return text[end] in BOUNDARY_CHARS


def _is_preceded_by_year(text: str, start: int) -> bool:
    """Require a year number immediately before the marker (possibly after punctuation)."""
    prefix = text[:start].rstrip("".join(BOUNDARY_CHARS))
    return bool(prefix) and prefix[-1].isdigit()


def _spans_overlap(start_a: int, end_a: int, start_b: int, end_b: int) -> bool:
    return start_a < end_b and start_b < end_a


def _is_valid_year_marker(text: str, start: int, end: int) -> bool:
    return (
        _has_valid_start_boundary(text, start)
        and _has_valid_end_boundary(text, end)
        and _is_preceded_by_year(text, start)
    )


def _find_year_markers(text: str, token_pattern: re.Pattern[str], replacement: str) -> list[tuple[int, int, str, str]]:
    matches: list[tuple[int, int, str, str]] = []
    for match in token_pattern.finditer(text):
        start, end = match.start(), match.end()
        if _is_valid_year_marker(text, start, end):
            matches.append((start, end, match.group(0), replacement))
    return matches


def _normalize_context(text: str) -> str:
    return " ".join(text.split())


def _context_snippet(
    text: str, start: int, end: int, replacement: str, radius: int = DEFAULT_CONTEXT_CHARS
) -> tuple[str, str]:
    before_start = max(0, start - radius)
    after_end = min(len(text), end + radius)
    prefix = "..." if before_start > 0 else ""
    suffix = "..." if after_end < len(text) else ""
    snippet = text[before_start:after_end]
    rel_start = start - before_start
    rel_end = end - before_start
    before = prefix + snippet + suffix
    after = prefix + snippet[:rel_start] + replacement + snippet[rel_end:] + suffix
    return _normalize_context(before), _normalize_context(after)


def replace_ce_bce_in_text(text: str, context_chars: int = DEFAULT_CONTEXT_CHARS) -> tuple[str, list[TextReplacement]]:
    """Replace standalone CE/BCE year markers with AD/BC."""
    if not text:
        return text, []

    bce_matches = _find_year_markers(text, BCE_TOKEN, "BC")
    bce_spans = [(start, end) for start, end, _, _ in bce_matches]

    ce_matches = []
    for start, end, original, replacement in _find_year_markers(text, CE_TOKEN, "AD"):
        if any(_spans_overlap(start, end, bce_start, bce_end) for bce_start, bce_end in bce_spans):
            continue
        ce_matches.append((start, end, original, replacement))

    matches = bce_matches + ce_matches
    if not matches:
        return text, []

    matches.sort(key=lambda item: item[0])

    replacements: list[TextReplacement] = []
    for start, end, original, replacement in matches:
        context_before, context_after = _context_snippet(text, start, end, replacement, radius=context_chars)
        replacements.append(
            TextReplacement(
                original=original,
                replacement=replacement,
                context_before=context_before,
                context_after=context_after,
            )
        )

    updated = text
    for start, end, _original, replacement in reversed(matches):
        updated = updated[:start] + replacement + updated[end:]

    return updated, replacements
