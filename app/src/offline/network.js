/*
  Are we online?
  ==============
  navigator.onLine only knows whether there is a network at all; a phone on
  a captive portal or a weak signal says "online" while nothing gets
  through. So the app is "offline" when the browser says so, or when API
  requests have just failed for want of a connection. The next request that
  gets an answer (or the browser's `online` event) brings it back.
*/
import { reactive } from 'vue';

export const network = reactive({
  // What the browser reports.
  browserOnline:
    typeof navigator === 'undefined' ? true : navigator.onLine !== false,
  // Requests are failing although the browser reports a network.
  unreachable: false,
  // When the app went offline (ms), for "offline since".
  since: null,
  get online() {
    return this.browserOnline && !this.unreachable;
  },
});

const listeners = new Set();

export function onConnectivityChange(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

let wasOnline = network.online;

function notify() {
  const online = network.online;
  if (online === wasOnline) return;
  wasOnline = online;
  network.since = online ? null : Date.now();
  listeners.forEach((listener) => {
    try {
      listener(online);
    } catch {
      // A listener's failure is its own.
    }
  });
}

export function reportReachable() {
  if (network.unreachable) {
    network.unreachable = false;
    notify();
  }
}

let probeTimer = null;
let probing = false;

export function reportUnreachable() {
  if (!network.browserOnline || network.unreachable) return;
  network.unreachable = true;
  notify();
  scheduleProbe();
}

// While "unreachable", check now and then whether the API answers again.
function scheduleProbe(delay = 15000) {
  if (probeTimer || typeof window === 'undefined') return;
  const next = Math.min(Math.max(delay * 2, 15000), 120000);
  probeTimer = window.setTimeout(async () => {
    probeTimer = null;
    if (!network.unreachable || probing) return;
    if (!network.browserOnline) {
      scheduleProbe(next);
      return;
    }
    probing = true;
    try {
      const base = import.meta.env.VITE_API_URL || '/';
      const response = await window.fetch(
        `${base}api/v1/content_changes?since=0`,
        {
          cache: 'no-store',
        }
      );
      if (response.ok) {
        reportReachable();
        return;
      }
    } catch {
      // Still nothing.
    } finally {
      probing = false;
    }
    scheduleProbe(next);
  }, delay);
}

// Back in front (a request cut off as the app went to the background can be
// what made it "unreachable"): check now rather than wait for the timer.
function probeNow() {
  if (!network.unreachable || probing || typeof window === 'undefined') return;
  window.clearTimeout(probeTimer);
  probeTimer = null;
  scheduleProbe(0);
}

export function isNetworkFailure(error) {
  if (!error) return false;
  if (error.isOffline) return true;
  if (error.response) return false;
  if (error.code === 'ERR_CANCELED' || error.name === 'CanceledError')
    return false;
  return true;
}

export function installNetworkListeners() {
  if (typeof window === 'undefined') return;
  window.addEventListener('online', () => {
    network.browserOnline = true;
    network.unreachable = false;
    notify();
  });
  window.addEventListener('offline', () => {
    network.browserOnline = false;
    notify();
  });
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') probeNow();
  });
}

// Tests only.
export function setBrowserOnlineForTests(online) {
  network.browserOnline = online;
  network.unreachable = false;
  notify();
}
