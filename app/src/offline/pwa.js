/*
  The installable web app
  =======================
  On the web (not in the iOS and Android apps, which carry their own shell):
  - registers the service worker (dist/sw.js, see serviceWorker.js), in
    production builds;
  - offers a new version once it has downloaded: a toast with Reload, so a
    page is never swapped out mid-prayer;
  - keeps the browser's install prompt for the Offline panel and the menu,
    and knows when Safari needs "Add to Home Screen" instead;
  - asks for background refreshes where the browser allows them.
*/
import { reactive } from 'vue';
import { Capacitor } from '@capacitor/core';
import { toast } from '@/ui/feedback';
import { resetStoredIndex } from './cacheAdapter';
import { onConnectivityChange } from './network';
import { isInstalledApp } from './preferences';
import { requestSync, syncState } from './sync';

const SYNC_TAG = 'offline-refresh';
const PERIODIC_MIN_INTERVAL = 12 * 3600 * 1000;
const UPDATE_CHECK_MS = 60 * 60 * 1000;

function isIosBrowser() {
  if (typeof navigator === 'undefined') return false;
  const ua = navigator.userAgent || '';
  const iOS =
    /iphone|ipad|ipod/i.test(ua) ||
    (/macintosh/i.test(ua) && navigator.maxTouchPoints > 1);
  return iOS && !Capacitor.isNativePlatform();
}

export const pwaState = reactive({
  supported: false,
  installed: isInstalledApp(),
  // The browser offered its install prompt (Chrome, Edge, Android).
  canPrompt: false,
  // Safari on iPhone and iPad: installed with Share, then Add to Home Screen.
  iosManual: false,
  updateReady: false,
  backgroundSync: 'unsupported', // unsupported | on | off
});

let deferredPrompt = null;
let registration = null;
let reloading = false;
let lastUpdateCheck = 0;

export async function promptInstall() {
  if (!deferredPrompt) return 'unavailable';
  deferredPrompt.prompt();
  const choice = await deferredPrompt.userChoice.catch(() => null);
  deferredPrompt = null;
  pwaState.canPrompt = false;
  return choice?.outcome || 'dismissed';
}

export function applyUpdate() {
  const waiting = registration?.waiting;
  if (!waiting) {
    window.location.reload();
    return;
  }
  waiting.postMessage({ type: 'SKIP_WAITING' });
}

function offerUpdate() {
  if (pwaState.updateReady) return;
  pwaState.updateReady = true;
  toast.info({
    title: 'A new version is ready',
    message: 'Reload when you’re ready; your place is kept.',
    link: { label: 'Reload now', action: applyUpdate },
    duration: 0,
  });
}

function watchForUpdates(reg) {
  if (reg.waiting && navigator.serviceWorker.controller) offerUpdate();
  reg.addEventListener('updatefound', () => {
    const worker = reg.installing;
    if (!worker) return;
    worker.addEventListener('statechange', () => {
      // A first install needs no reload; a replacement waits for one.
      if (worker.state === 'installed' && navigator.serviceWorker.controller) {
        offerUpdate();
      }
    });
  });
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    if (reloading || !pwaState.updateReady) return;
    reloading = true;
    window.location.reload();
  });
}

function checkForUpdate() {
  if (!registration || Date.now() - lastUpdateCheck < UPDATE_CHECK_MS) return;
  lastUpdateCheck = Date.now();
  registration.update().catch(() => {});
}

async function enableBackgroundSync(reg) {
  if (!('periodicSync' in reg)) return;
  try {
    const status = await navigator.permissions.query({
      name: 'periodic-background-sync',
    });
    if (status.state !== 'granted') {
      pwaState.backgroundSync = 'off';
      return;
    }
    await reg.periodicSync.register(SYNC_TAG, {
      minInterval: PERIODIC_MIN_INTERVAL,
    });
    pwaState.backgroundSync = 'on';
  } catch {
    pwaState.backgroundSync = 'off';
  }
}

// When the connection drops mid-download, the service worker finishes the
// job as soon as it returns, even if the tab has closed (Chrome and Edge).
function finishWhenBackOnline(online) {
  if (online || !registration?.sync) return;
  if (
    syncState.status !== 'syncing' &&
    syncState.readyDays >= syncState.plannedDays
  )
    return;
  registration.sync.register(SYNC_TAG).catch(() => {});
}

export function installPwa() {
  if (typeof window === 'undefined' || Capacitor.isNativePlatform()) return;

  pwaState.iosManual = isIosBrowser() && !pwaState.installed;

  window.addEventListener('beforeinstallprompt', (event) => {
    event.preventDefault();
    deferredPrompt = event;
    pwaState.canPrompt = true;
  });
  window.addEventListener('appinstalled', () => {
    pwaState.installed = true;
    pwaState.canPrompt = false;
    deferredPrompt = null;
    // An installed app keeps a month by default.
    requestSync('preferences');
  });

  if (!('serviceWorker' in navigator) || !import.meta.env.PROD) return;
  if (import.meta.env.VITE_SERVICE_WORKER === 'false') return;
  pwaState.supported = true;

  const register = async () => {
    try {
      registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/',
      });
      lastUpdateCheck = Date.now();
      watchForUpdates(registration);
      if (pwaState.installed) enableBackgroundSync(registration);
    } catch {
      pwaState.supported = false;
    }
  };
  if (document.readyState === 'complete') register();
  else window.addEventListener('load', register, { once: true });

  navigator.serviceWorker.addEventListener('message', (event) => {
    if (event.data?.type === 'OFFLINE_BACKGROUND_SYNCED') {
      // It wrote to storage behind this page's back.
      resetStoredIndex();
      requestSync('background');
    }
  });
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') checkForUpdate();
  });
  onConnectivityChange(finishWhenBackOnline);
}
