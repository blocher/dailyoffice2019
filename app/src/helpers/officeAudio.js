/*
  Fetching generated audio
  ========================
  Offices (Office.vue) and the Readings page ask the API for one combined
  audio track. Audio that isn't built yet is prepared in the background: the
  API answers 202 with audio.status "preparing" and a retry delay, and the
  page keeps asking until it is ready.
*/
import { getCachedClientId } from '@/helpers/clientId';

// How long to keep polling while the server prepares audio.
export const AUDIO_PREPARE_TIMEOUT_MS = 10 * 60 * 1000;

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
// fetched from, and append the anonymous client id so the backend can
// attribute the "audio loaded" event (<audio> can't send custom headers).
export function resolveAudioUrl(rawUrl) {
  if (!rawUrl) {
    return rawUrl;
  }
  try {
    const path = new window.URL(rawUrl, window.location.origin).pathname;
    const base = (import.meta.env.VITE_API_URL || '/').replace(/\/$/, '');
    const clientId = getCachedClientId();
    const query = clientId ? `?cid=${encodeURIComponent(clientId)}` : '';
    return `${base}/${path.replace(/^\//, '')}${query}`;
  } catch {
    return rawUrl;
  }
}

// The combined track ([url, path, sections, lines, words]) for an
// include_audio_links URL, or [] when it can't be had. `isStopped` ends the
// polling early (the page was left).
export async function fetchAudioTrack(http, url, isStopped = () => false) {
  const giveUpAt = Date.now() + AUDIO_PREPARE_TIMEOUT_MS;
  try {
    for (;;) {
      const data = await http.get(url);
      const audio = data.data.audio || {};
      if (audio.status === 'preparing') {
        if (isStopped() || Date.now() >= giveUpAt) {
          return [];
        }
        await waitForRetry(audio.retry_after);
        if (isStopped()) {
          return [];
        }
        continue;
      }
      const singleTrack = audio.single_track;
      if (Array.isArray(singleTrack) && singleTrack.length) {
        singleTrack[0] = resolveAudioUrl(singleTrack[0]);
        return singleTrack;
      }
      return [];
    }
  } catch {
    return [];
  }
}
