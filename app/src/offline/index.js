/*
  Offline mode
  ============
  The app keeps the coming days of offices on the device and keeps them up
  to date, so it opens and prays without a connection: in a browser tab, as
  an installed web app, and in the iOS and Android apps.

    db.js           IndexedDB storage
    keys.js         which requests are stored, and their keys
    urls.js         API addresses (shared with the pages)
    cacheAdapter.js axios adapter: answers from storage when it should
    network.js      online / offline
    sync.js         downloads the days ahead; keeps them fresh
    staleness.js    the API's content change log, applied to storage
    audio.js        office audio for offline listening (opt-in)
    preferences.js  offline preferences
    viewQueue.js    office views prayed offline, reported later
    pwa.js          service worker, install, updates (web only)

  installOffline() is called once from main.js; the Offline panel
  (components/OfflinePanel.vue) shows the state and the preferences.
*/
import { watch } from 'vue';
import { App as CapacitorApp } from '@capacitor/app';
import { Capacitor } from '@capacitor/core';
import { DynamicStorage } from '@/helpers/storage';
import { installCacheAdapter } from './cacheAdapter';
import {
  installNetworkListeners,
  network,
  onConnectivityChange,
} from './network';
import { loadOfflinePrefs, offlinePrefs } from './preferences';
import { configureSync, loadSyncStatus, requestSync, syncIfDue } from './sync';
import { flushViews } from './viewQueue';
import { friendlyDate } from './format';
import { syncState } from './sync';
import { openPanel, panels } from '@/helpers/panels';
import { toast } from '@/ui/feedback';

export { network } from './network';
export {
  syncState,
  requestSync,
  clearDownloads,
  canPrayOfflineWith,
} from './sync';
export {
  offlinePrefs,
  setOfflinePref,
  effectiveDays,
  defaultDays,
  DAY_CHOICES,
} from './preferences';

async function readContext(store) {
  const settings = store.state.settings;
  if (!settings || typeof settings !== 'object') return null;
  let extraCollects;
  try {
    extraCollects = JSON.parse(
      (await DynamicStorage.getItem('extraCollects')) || 'null'
    );
  } catch {
    extraCollects = null;
  }
  const [translation, psalms, style] = await Promise.all([
    DynamicStorage.getItem('readings_translation'),
    DynamicStorage.getItem('psalms_translation'),
    DynamicStorage.getItem('psalm_style'),
  ]);
  const readings =
    translation && translation !== 'undefined'
      ? {
          translation,
          psalms: psalms || settings.language_style || 'contemporary',
          style: style || settings.psalm_style || 'whole_verse',
        }
      : null;
  return { settings: { ...settings }, extraCollects, readings };
}

function msUntilTomorrow() {
  const now = new Date();
  const next = new Date(now);
  next.setDate(now.getDate() + 1);
  next.setHours(0, 2, 0, 0);
  return next - now;
}

let lastAnnounced = 0;

// Once in a while, not on every flicker of the signal.
function announceOffline() {
  try {
    lastAnnounced = Math.max(
      lastAnnounced,
      Number(window.sessionStorage.getItem('offlineAnnounced')) || 0
    );
  } catch {
    // Session storage unavailable: the in-memory time stands.
  }
  if (network.online || panels.offline) return;
  if (Date.now() - lastAnnounced < 10 * 60 * 1000) return;
  lastAnnounced = Date.now();
  try {
    window.sessionStorage.setItem('offlineAnnounced', String(lastAnnounced));
  } catch {
    // As above.
  }
  const through = syncState.readyThrough;
  toast.info({
    title: 'You’re offline',
    message: through
      ? `Your offices are downloaded through ${friendlyDate(through)}.`
      : 'Pages you’ve opened before are still here.',
    link: { label: 'What’s downloaded', action: () => openPanel('offline') },
  });
}

let installed = false;

export function installOffline({ store }) {
  if (installed) return;
  installed = true;
  installCacheAdapter();
  installNetworkListeners();
  configureSync({ getContext: () => readContext(store) });

  const ready = Promise.all([loadOfflinePrefs(), loadSyncStatus()]);

  // The first run waits for the page to settle, then for settings.
  let started = false;
  const start = async () => {
    if (started) return;
    started = true;
    await ready;
    const begin = () => requestSync('start');
    if (typeof window !== 'undefined' && window.requestIdleCallback) {
      window.requestIdleCallback(begin, { timeout: 4000 });
    } else {
      window.setTimeout(begin, 2500);
    }
  };

  watch(
    () => store.state.settings,
    (settings, previous) => {
      if (!settings) return;
      if (!started) {
        start();
        return;
      }
      if (previous && JSON.stringify(settings) === JSON.stringify(previous))
        return;
      window.clearTimeout(watchTimer);
      watchTimer = window.setTimeout(() => requestSync('settings'), 1200);
    },
    { immediate: true }
  );
  let watchTimer = null;

  watch(
    () => [
      offlinePrefs.days,
      offlinePrefs.family,
      offlinePrefs.audio,
      offlinePrefs.audioOffices.join(),
    ],
    () => {
      if (!offlinePrefs.loaded || !started) return;
      window.clearTimeout(prefsTimer);
      prefsTimer = window.setTimeout(() => requestSync('preferences'), 600);
    }
  );
  let prefsTimer = null;

  onConnectivityChange((online) => {
    if (online) {
      flushViews();
      requestSync('online');
    } else {
      announceOffline();
    }
  });
  // Opened without a connection.
  if (!network.online) {
    ready.then(() => window.setTimeout(announceOffline, 3500));
  }

  if (typeof document !== 'undefined') {
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible' && network.online)
        syncIfDue('resume');
    });
  }
  if (Capacitor.isNativePlatform()) {
    Promise.resolve(
      CapacitorApp.addListener('appStateChange', ({ isActive }) => {
        if (isActive && network.online) syncIfDue('resume');
      })
    ).catch(() => {});
  }

  // A new day: move the window along.
  const daily = () => {
    window.setTimeout(() => {
      requestSync('new-day');
      daily();
    }, msUntilTomorrow());
  };
  daily();
}
