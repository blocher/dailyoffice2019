/*
  Fetching generated audio
  ========================
  Offices (Office.vue) and the Readings page ask the API for one combined
  audio track. Audio that isn't built yet is prepared in the background: the
  API answers 202 with audio.status "preparing" and a retry delay, and the
  page keeps asking until it is ready. A dropped request, a server error or an
  answer with no track is asked again a few times before the page says audio
  is unavailable.
*/
// How long to keep polling while the server prepares audio.
export const AUDIO_PREPARE_TIMEOUT_MS = 10 * 60 * 1000;
// Delays before asking again after a failed request or an answer with no
// track; after the last one the page gives up on audio.
export const AUDIO_FETCH_RETRY_DELAYS_MS = [3000, 10000, 30000];

// Audio is generated from three days ago through nine days ahead.
export function isWithinAudioWindow(date, today = new Date()) {
  const start = new Date(today);
  start.setHours(0, 0, 0, 0);
  start.setDate(start.getDate() - 3);
  const end = new Date(today);
  end.setHours(0, 0, 0, 0);
  end.setDate(end.getDate() + 9);
  end.setHours(23, 59, 59, 999);
  return date >= start && date <= end;
}

// Wait the server's suggested delay (seconds), clamped to 2–30 s.
export function waitForRetry(seconds) {
  const delay = Math.min(Math.max(Number(seconds) || 5, 2), 30) * 1000;
  return new Promise((resolve) => window.setTimeout(resolve, delay));
}

// The backend builds the track URL from its own address, which may not be
// reachable from the client. Resolve it against the API host the page was
// fetched from. The URL is the same for every listener, so Cloudflare serves
// it from its cache; listening is counted by the page's audio_play event.
export function resolveAudioUrl(rawUrl) {
  if (!rawUrl) {
    return rawUrl;
  }
  try {
    const path = new window.URL(rawUrl, window.location.origin).pathname;
    const base = (import.meta.env.VITE_API_URL || '/').replace(/\/$/, '');
    return `${base}/${path.replace(/^\//, '')}`;
  } catch {
    return rawUrl;
  }
}

// Network failures, timeouts, rate limits and server errors may pass; a 4xx
// answer will not change by asking again.
function isTransientFailure(error) {
  const status = error?.response?.status;
  return !status || status >= 500 || status === 408 || status === 429;
}

// The combined track ([url, path, sections, lines, words]) for an
// include_audio_links URL, or [] when it can't be had. `isStopped` ends the
// polling early (the page was left).
export async function fetchAudioTrack(http, url, isStopped = () => false) {
  const giveUpAt = Date.now() + AUDIO_PREPARE_TIMEOUT_MS;
  let failures = 0;
  for (;;) {
    let audio = null;
    try {
      const data = await http.get(url);
      audio = data?.data?.audio || {};
    } catch (error) {
      if (!isTransientFailure(error)) return [];
    }
    if (audio?.status === 'preparing') {
      if (isStopped() || Date.now() >= giveUpAt) {
        return [];
      }
      await waitForRetry(audio.retry_after);
      if (isStopped()) {
        return [];
      }
      continue;
    }
    const singleTrack = audio?.single_track;
    if (Array.isArray(singleTrack) && singleTrack.length) {
      singleTrack[0] = resolveAudioUrl(singleTrack[0]);
      return singleTrack;
    }
    if (
      failures >= AUDIO_FETCH_RETRY_DELAYS_MS.length ||
      isStopped() ||
      Date.now() >= giveUpAt
    ) {
      return [];
    }
    await new Promise((resolve) =>
      window.setTimeout(resolve, AUDIO_FETCH_RETRY_DELAYS_MS[failures])
    );
    failures += 1;
    if (isStopped()) {
      return [];
    }
  }
}
