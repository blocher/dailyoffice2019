/*
  Office audio track checks
  =========================
  The office audio is one long mp3 with a timeline (sections, lines, words)
  computed on the server. If the file is cut short (an interrupted encode
  cached by a CDN or browser), the timeline still runs past the real end of
  the audio. These helpers let the player notice that instead of quietly
  stopping or restarting from the top.
*/

// The timeline is scaled to the file on the server, so a complete track ends
// within a second or two of its last line. Ten seconds leaves room for
// rounding and trailing silence while still catching a missing ending.
export const EARLY_END_SECONDS = 10;
// A section the media can't reach by more than this is past the file's end.
export const BEYOND_END_SECONDS = 1;

// Where the timeline says the spoken office ends, in seconds (0 if unknown).
export function timelineEnd(sections = [], lines = []) {
  let end = 0;
  for (const line of lines) {
    const value = Number(line?.end_time);
    if (Number.isFinite(value) && value > end) end = value;
  }
  for (const section of sections) {
    const value = Number(section?.start_time);
    if (Number.isFinite(value) && value > end) end = value;
  }
  return end;
}

// True when playback stopped well before the timeline's last line.
export function endedEarly(
  endedAt,
  expectedEnd,
  threshold = EARLY_END_SECONDS
) {
  if (!Number.isFinite(endedAt) || !Number.isFinite(expectedEnd)) return false;
  return expectedEnd - endedAt > threshold;
}

// How long playback may sit buffering with no data arriving before the
// player reloads the track and carries on from the same place, one delay per
// attempt. After the last one the listener gets the Retry button instead.
export const STALL_RESUME_DELAYS_MS = [10000, 20000, 40000];
// Seconds of playback after an automatic resume that count as recovered, so
// a later stall starts again from the first (shortest) delay.
export const STALL_RECOVERED_SECONDS = 30;

// True when a seek target lies past the end of a track of known length.
export function beyondTrackEnd(
  target,
  duration,
  tolerance = BEYOND_END_SECONDS
) {
  if (!Number.isFinite(target) || !Number.isFinite(duration)) return false;
  if (duration <= 0) return false;
  return target > duration + tolerance;
}

// The same track URL with a fresh query value, so neither the browser nor
// the CDN can answer from a stale (truncated) cached copy.
export function freshTrackUrl(url, token = Date.now()) {
  if (!url) return url;
  try {
    const parsed = new window.URL(url, window.location.href);
    parsed.searchParams.set('reload', String(token));
    return parsed.toString();
  } catch {
    const separator = url.includes('?') ? '&' : '?';
    return `${url}${separator}reload=${encodeURIComponent(String(token))}`;
  }
}
