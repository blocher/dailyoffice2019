"""Asynchronous Gemini Batch TTS for pre-warming the office audio cache.

The Batch API runs at roughly half the price of interactive synthesis but is
asynchronous (target turnaround up to ~24h), so it is used *only* by the
pre-warm command, never for live requests. It reuses the exact request config,
PCM extraction, duration guardrails, and MP3 encoding as the real-time path so a
clip sounds identical however it was produced.

Robustness: any chunk the batch does not produce (job failure, rejected/runaway
clip, straggler) is simply left uncached, and the office's next render
synthesizes it in real time. The batch is a cost optimization, not a
correctness dependency.

Docs: https://ai.google.dev/gemini-api/docs/batch-api
"""

from __future__ import annotations

import base64
import json
import logging
import time

from django.conf import settings

from office.audio.gemini import (
    BatchChunk,
    _check_duration_plausible,
    _extract_pcm,
    _genai_client,
    build_generate_content_config,
    encode_pcm_to_mp3,
    gemini_model,
)

logger = logging.getLogger(__name__)

# Terminal batch-job states (anything else means "still running").
TERMINAL_STATES = {
    "JOB_STATE_SUCCEEDED",
    "JOB_STATE_FAILED",
    "JOB_STATE_CANCELLED",
    "JOB_STATE_EXPIRED",
    "JOB_STATE_PAUSED",
}


def _int_setting(name, default, minimum=1):
    value = getattr(settings, name, None)
    try:
        return max(int(value), minimum)
    except (TypeError, ValueError):
        return default


def batch_group_size():
    # Chunks per batch job. Kept modest so a single job's inline response payload
    # (which carries the base64 audio) stays manageable.
    return _int_setting("GEMINI_BATCH_SIZE", 100)


def batch_poll_seconds():
    return _int_setting("GEMINI_BATCH_POLL_SECONDS", 30)


def batch_timeout_seconds():
    # Per-job wall-clock ceiling. Batch targets <24h; default to 6h so a stuck
    # job doesn't hang a nightly cron indefinitely.
    return _int_setting("GEMINI_BATCH_TIMEOUT_SECONDS", 6 * 60 * 60)


def _grouped(items, size):
    for start in range(0, len(items), size):
        yield items[start : start + size]


def _state_name(job):
    state = getattr(job, "state", None)
    return getattr(state, "name", None) or (str(state) if state is not None else "")


def _poll_until_done(client, job):
    deadline = time.monotonic() + batch_timeout_seconds()
    while _state_name(job) not in TERMINAL_STATES:
        if time.monotonic() > deadline:
            raise TimeoutError(
                f"Gemini batch job {getattr(job, 'name', '?')} did not finish within "
                f"{batch_timeout_seconds()}s (state={_state_name(job)})"
            )
        time.sleep(batch_poll_seconds())
        job = client.batches.get(name=job.name)
    return job


def _submit_group(client, group):
    requests = [
        {
            "contents": chunk.prompt,
            "config": build_generate_content_config(chunk.roles, chunk.voices, chunk.spoken_chars),
        }
        for chunk in group
    ]
    return client.batches.create(
        model=gemini_model(),
        src=requests,
        config={"display_name": "dailyoffice-tts-prewarm"},
    )


def _extract_pcm_from_json(response_json):
    """Extract raw PCM from a batch output-file response record (plain JSON).

    File-based batch output embeds the audio as base64 under inlineData.data;
    the SDK's camelCase/snake_case can vary, so accept both.
    """
    candidates = (response_json or {}).get("candidates") or []
    candidate = candidates[0] if candidates else {}
    finish_reason = candidate.get("finishReason") or candidate.get("finish_reason") or ""
    parts = ((candidate.get("content") or {}).get("parts")) or []
    inline = {}
    if parts:
        inline = parts[0].get("inlineData") or parts[0].get("inline_data") or {}
    data = inline.get("data")
    if not data:
        raise RuntimeError(f"Batch response contained no audio (finish_reason={finish_reason or None})")
    if finish_reason == "MAX_TOKENS":
        raise RuntimeError("Batch response hit the output token cap (finish_reason=MAX_TOKENS)")
    if isinstance(data, str):
        data = base64.b64decode(data)
    return data


def _iter_file_results(client, group, file_name):
    """Yield (chunk, pcm_or_None, error) from a batch output JSONL file.

    Records are in submission order, so we pair them positionally with `group`.
    """
    raw = client.files.download(file=file_name)
    if isinstance(raw, bytes):
        text = raw.decode("utf-8")
    else:
        text = str(raw)
    lines = [line for line in text.splitlines() if line.strip()]
    for chunk, line in zip(group, lines):
        try:
            record = json.loads(line)
            response_json = record.get("response") if isinstance(record, dict) else None
            if response_json is None:
                raise RuntimeError(
                    f"batch record error: {record.get('error') if isinstance(record, dict) else record}"
                )
            yield chunk, _extract_pcm_from_json(response_json), None
        except Exception as exc:  # noqa: BLE001 — per-chunk failures are tolerated
            yield chunk, None, exc


def _iter_inline_results(group, inlined_responses):
    for chunk, item in zip(group, inlined_responses):
        response = getattr(item, "response", None)
        error = getattr(item, "error", None)
        if response is None:
            yield chunk, None, error or "no response"
            continue
        try:
            yield chunk, _extract_pcm(response), None
        except Exception as exc:  # noqa: BLE001
            yield chunk, None, exc


def _iter_group_results(client, group, job):
    dest = getattr(job, "dest", None)
    inlined = getattr(dest, "inlined_responses", None) if dest is not None else None
    if inlined:
        yield from _iter_inline_results(group, inlined)
        return
    file_name = getattr(dest, "file_name", None) if dest is not None else None
    if file_name:
        yield from _iter_file_results(client, group, file_name)
        return
    raise RuntimeError("Gemini batch job produced neither inline responses nor an output file")


def chunk_to_meta(chunk):
    """Minimal, JSON-serializable info needed to retrieve+write a chunk later."""
    return {
        "cache_key": chunk.cache_key,
        "file_path": chunk.file_path,
        "spoken_chars": chunk.spoken_chars,
    }


def _chunk_from_meta(meta):
    # prompt/roles/voices are only needed at submission time, not for retrieval.
    return BatchChunk(
        cache_key=meta.get("cache_key", ""),
        prompt="",
        file_path=meta.get("file_path", ""),
        spoken_chars=int(meta.get("spoken_chars") or 0),
    )


def _write_completed_results(client, group, job, summary):
    """Write clips from a SUCCEEDED job; tally into summary. Never raises."""
    try:
        results = list(_iter_group_results(client, group, job))
    except Exception:  # noqa: BLE001
        logger.exception("Could not read results for Gemini batch job %s", getattr(job, "name", "?"))
        summary["failed"] += len(group)
        return summary

    for chunk, pcm, error in results:
        if error is not None or not pcm:
            summary["failed"] += 1
            logger.warning("Skipping batch clip %s: %s", chunk.cache_key, error or "no audio")
            continue
        try:
            _check_duration_plausible(pcm, chunk.spoken_chars)
            encode_pcm_to_mp3(pcm, chunk.file_path)
            summary["written"] += 1
        except Exception as exc:  # noqa: BLE001 — reject implausible/undecodable audio
            summary["failed"] += 1
            logger.warning("Rejected batch clip %s: %s", chunk.cache_key, exc)
    return summary


def submit_chunks(chunks):
    """Submit chunks as batch jobs WITHOUT waiting for completion.

    Returns a list of {"job_name", "model_name", "chunks": [meta, ...]} for the
    jobs that were accepted, so the caller can persist them for later retrieval.
    """
    chunks = [chunk for chunk in chunks if isinstance(chunk, BatchChunk) and chunk.prompt]
    submitted = []
    if not chunks:
        return submitted

    client = _genai_client()
    model = gemini_model()
    for group in _grouped(chunks, batch_group_size()):
        try:
            job = _submit_group(client, group)
        except Exception:  # noqa: BLE001 — a rejected submission just leaves cache misses
            logger.exception("Failed to submit Gemini batch job for %s chunk(s)", len(group))
            continue
        job_name = getattr(job, "name", None)
        if not job_name:
            logger.warning("Gemini batch submission returned no job name; skipping %s chunk(s)", len(group))
            continue
        submitted.append(
            {
                "job_name": job_name,
                "model_name": model,
                "chunks": [chunk_to_meta(chunk) for chunk in group],
            }
        )
    return submitted


def fetch_job(job_name, chunk_meta):
    """Poll a submitted job once (no blocking) and write clips if it finished.

    Returns {"state", "terminal", "succeeded", "written", "failed"}. Writes any
    successful clips to the cache; never raises for per-chunk problems.
    """
    client = _genai_client()
    job = client.batches.get(name=job_name)
    state = _state_name(job)
    summary = {"state": state, "terminal": False, "succeeded": False, "written": 0, "failed": 0}
    if state not in TERMINAL_STATES:
        return summary

    summary["terminal"] = True
    if state != "JOB_STATE_SUCCEEDED":
        logger.warning("Gemini batch job %s ended in state %s", job_name, state)
        summary["failed"] = len(chunk_meta)
        return summary

    summary["succeeded"] = True
    group = [_chunk_from_meta(meta) for meta in chunk_meta]
    write_summary = {"written": 0, "failed": 0}
    _write_completed_results(client, group, job, write_summary)
    summary["written"] = write_summary["written"]
    summary["failed"] = write_summary["failed"]
    return summary


def run_batch_synthesis(chunks):
    """Synchronous submit+poll+write for the all-in-one `--batch sync` mode.

    Returns a summary dict: {"requested", "written", "failed"}. Never raises for
    per-chunk problems — those clips are just left for real-time synthesis.
    """
    chunks = [chunk for chunk in chunks if isinstance(chunk, BatchChunk) and chunk.prompt]
    summary = {"requested": len(chunks), "written": 0, "failed": 0}
    if not chunks:
        return summary

    client = _genai_client()
    for group in _grouped(chunks, batch_group_size()):
        try:
            job = _submit_group(client, group)
            job = _poll_until_done(client, job)
        except Exception:  # noqa: BLE001 — a whole-job failure only costs cache misses
            logger.exception("Gemini batch job failed for a group of %s chunk(s)", len(group))
            summary["failed"] += len(group)
            continue

        state = _state_name(job)
        if state != "JOB_STATE_SUCCEEDED":
            logger.warning("Gemini batch job %s ended in state %s", getattr(job, "name", "?"), state)
            summary["failed"] += len(group)
            continue

        _write_completed_results(client, group, job, summary)

    return summary
