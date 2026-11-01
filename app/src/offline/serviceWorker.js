/* global self, caches, clients, indexedDB, fetch, URL, Response */
/*
  Service worker (web and installed web app only)
  ===============================================
  Built into dist/sw.js by the offlineServiceWorker plugin in vite.config.mjs,
  which fills in __VERSION__ and __PRECACHE__ (the app shell: index.html,
  every script and stylesheet, the Caslon fonts, the icons). The iOS and
  Android apps carry the shell themselves and don't use this.

  - The app shell answers from the cache, so the app opens offline.
  - Other fonts (the alternative reading typefaces, Google's Chinese faces)
    are kept the first time they're used.
  - API requests are left to the app (src/offline/cacheAdapter.js).
  - In the background, where the browser allows (Chrome and Edge, mostly
    for an installed app), it follows the download plan the app wrote
    (src/offline/sync.js): `periodicsync` keeps the days ahead fresh, and
    `sync` finishes downloads once a lost connection returns.
  - A new version waits until the reader chooses to reload (src/offline/pwa.js).

  The IndexedDB layout and the record format must match src/offline/db.js
  and src/offline/cacheAdapter.js.
*/

const VERSION = '__VERSION__';
const PRECACHE = __PRECACHE__; // eslint-disable-line no-undef
const SHELL_CACHE = `shell-${VERSION}`;
const RUNTIME_CACHE = 'runtime-assets';
const FONT_CACHE = 'google-fonts';
const RUNTIME_LIMIT = 80;
// Google's Chinese faces come in many small pieces; keep the latest.
const FONT_LIMIT = 120;

const DB_NAME = 'dailyoffice-offline';
const DB_VERSION = 1;
const SCHEMA = 1;
const SYNC_TAG = 'offline-refresh';
const BACKGROUND_LIMIT = 80;

// A redirected answer can't answer a navigation (hosts send /index.html on
// to /), so keep a clean copy.
async function cleanCopy(response) {
  if (!response.redirected) return response;
  return new Response(await response.blob(), {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers,
  });
}

// A missing script or style can come back as the app's index.html with a
// 200 (the host's fallback for unknown paths); that is not worth keeping.
function isHtmlFor(path, response) {
  const type = response.headers.get('Content-Type') || '';
  return (
    type.includes('text/html') &&
    /\.[a-z0-9]+$/i.test(path) &&
    !path.endsWith('.html')
  );
}

// Built files carry a hash of their contents in their names (Vite's
// /assets/name-hash.js): one already kept by an earlier version is the same
// file, so a new version needn't download it again.
function isHashedAsset(path) {
  return /^\/assets\/[^/]+-[A-Za-z0-9_-]{8,}\.[a-z0-9]+$/.test(path);
}

self.addEventListener('install', (event) => {
  event.waitUntil(
    (async () => {
      const cache = await caches.open(SHELL_CACHE);
      await Promise.all(
        PRECACHE.map(async (path) => {
          if (isHashedAsset(path)) {
            const kept = await caches.match(path, { ignoreVary: true });
            if (kept?.ok) {
              await cache.put(path, kept);
              return;
            }
          }
          const response = await fetch(path, { cache: 'reload' });
          // A file not there yet (a deploy half done): fail the install, and
          // the version in use carries on until the next check.
          if (!response.ok || isHtmlFor(path, response))
            throw new Error(`Precache failed: ${path}`);
          await cache.put(path, await cleanCopy(response));
        })
      );
    })()
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    (async () => {
      // Old shells, and anything this worker doesn't use: the 2022 site's
      // Workbox worker (/service-worker.js) left caches behind.
      const kept = [SHELL_CACHE, RUNTIME_CACHE, FONT_CACHE];
      const names = await caches.keys();
      await Promise.all(
        names
          .filter((name) => !kept.includes(name))
          .map((name) => caches.delete(name))
      );
      await self.clients.claim();
    })()
  );
});

self.addEventListener('message', (event) => {
  if (event.data?.type === 'SKIP_WAITING') self.skipWaiting();
});

async function trim(cacheName, limit) {
  const cache = await caches.open(cacheName);
  const keys = await cache.keys();
  await Promise.all(
    keys
      .slice(0, Math.max(0, keys.length - limit))
      .map((key) => cache.delete(key))
  );
}

async function shellResponse(request) {
  const cache = await caches.open(SHELL_CACHE);
  // Hosts answer with Vary: Origin (or Accept-Encoding); the files are the
  // same whatever asked for them.
  return cache.match(request, { ignoreVary: true });
}

async function navigation(request) {
  // The app shell, at once; the network only when it isn't cached yet.
  const cached = await shellResponse('/');
  if (cached) return cached;
  try {
    return await fetch(request);
  } catch {
    return new Response('<h1>Offline</h1>', {
      status: 503,
      headers: { 'Content-Type': 'text/html' },
    });
  }
}

async function cacheFirst(request, cacheName) {
  const cached =
    (await shellResponse(request)) ||
    (await caches.match(request, { ignoreVary: true }));
  if (cached) return cached;
  const response = await fetch(request);
  const path = new URL(request.url).pathname;
  if (
    (response.ok && !isHtmlFor(path, response)) ||
    response.type === 'opaque'
  ) {
    const cache = await caches.open(cacheName);
    await cache.put(request, response.clone());
    trim(cacheName, RUNTIME_LIMIT);
  }
  return response;
}

async function staleWhileRevalidate(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request, { ignoreVary: true });
  const network = fetch(request)
    .then((response) => {
      // Only readable answers: an opaque one counts as megabytes against
      // the storage quota. (The stylesheet and the fonts are sent with CORS.)
      if (response.ok) {
        cache
          .put(request, response.clone())
          .then(() => trim(cacheName, FONT_LIMIT));
      }
      return response;
    })
    .catch(() => cached);
  return cached || network;
}

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);

  if (url.origin === self.location.origin) {
    if (url.pathname.startsWith('/api/')) return;
    if (request.mode === 'navigate') {
      // Files with an extension (sitemap.xml, robots.txt) are not pages.
      if (/\.[a-z0-9]+$/i.test(url.pathname) && !url.pathname.endsWith('.html'))
        return;
      event.respondWith(navigation(request));
      return;
    }
    if (url.pathname === '/sw.js') return;
    if (
      /\.(js|css|woff2?|png|ico|svg|webmanifest|json|jpg|webp)$/i.test(
        url.pathname
      )
    ) {
      event.respondWith(cacheFirst(request, RUNTIME_CACHE));
    }
    return;
  }

  if (
    url.hostname === 'fonts.googleapis.com' ||
    url.hostname === 'fonts.gstatic.com'
  ) {
    event.respondWith(staleWhileRevalidate(request, FONT_CACHE));
  }
});

/* ── Background downloads ─────────────────────────────────────────── */

function openDb() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      // The app creates the stores (src/offline/db.js upgrade()); keep in step.
      const db = request.result;
      if (!db.objectStoreNames.contains('responses')) {
        const responses = db.createObjectStore('responses', { keyPath: 'key' });
        responses.createIndex('date', 'date');
        responses.createIndex('profile', 'profile');
      }
      if (!db.objectStoreNames.contains('audio'))
        db.createObjectStore('audio', { keyPath: 'url' });
      if (!db.objectStoreNames.contains('meta')) db.createObjectStore('meta');
      if (!db.objectStoreNames.contains('views')) {
        db.createObjectStore('views', { keyPath: 'id', autoIncrement: true });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

function run(db, storeName, mode, action) {
  return new Promise((resolve, reject) => {
    const tx = db.transaction(storeName, mode);
    const request = action(tx.objectStore(storeName));
    let result;
    request.onsuccess = () => {
      result = request.result;
    };
    tx.oncomplete = () => resolve(result);
    tx.onerror = () => reject(tx.error);
    tx.onabort = () => reject(tx.error);
  });
}

function isoToday(offset = 0) {
  const date = new Date();
  date.setDate(date.getDate() + offset);
  const pad = (n) => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

function monthEnd(isoFirst) {
  const [year, month] = isoFirst.split('-').map(Number);
  const last = new Date(year, month, 0).getDate();
  return `${isoFirst.slice(0, 8)}${String(last).padStart(2, '0')}`;
}

// Keep the change list to 50 notes by folding the oldest together, as
// src/offline/staleness.js does: dropping one would unmark what it marked.
function fold(list, max = 50) {
  if (list.length <= max) return list;
  const folded = list.slice(0, list.length - max + 1);
  const merged = [];
  folded
    .flatMap((item) => item.dates || [])
    .sort((a, b) => (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0))
    .forEach(([first, last]) => {
      const previous = merged[merged.length - 1];
      if (previous && first <= previous[1]) {
        if (last > previous[1]) previous[1] = last;
      } else {
        merged.push([first, last]);
      }
    });
  const note = {
    at: Math.max(...folded.map((item) => item.at)),
    all: folded.some((item) => item.all),
    urgent: folded.some((item) => item.all && item.urgent),
    dates: merged,
  };
  return [note, ...list.slice(list.length - max + 1)];
}

// Same rule as src/offline/staleness.js.
function staleness(record, invalidations) {
  let result = null;
  for (const change of invalidations) {
    if (change.at <= record.fetchedAt) continue;
    if (record.date) {
      const end = record.kind === 'month' ? monthEnd(record.date) : record.date;
      const dated = (change.dates || []).some(
        ([first, last]) => first <= end && last >= record.date
      );
      if (dated) return 'hard';
    }
    if (!change.all) continue;
    if (change.urgent) return 'hard';
    result = 'soft';
  }
  return result;
}

async function backgroundRefresh() {
  const db = await openDb();
  const plan = await run(db, 'meta', 'readonly', (store) => store.get('plan'));
  if (!plan?.tasks?.length) return;
  let invalidations =
    (await run(db, 'meta', 'readonly', (store) =>
      store.get('invalidations')
    )) || [];

  const apiBase = new URL(plan.apiBase || '/', self.location.origin);
  // Content changes since the app last looked.
  try {
    const since =
      (await run(db, 'meta', 'readonly', (store) =>
        store.get('contentVersion')
      )) || 0;
    const response = await fetch(
      new URL(`api/v1/content_changes?since=${since}`, apiBase)
    );
    if (response.ok) {
      const summary = await response.json();
      // Never checked before (src/offline/sync.js does the same): what was
      // downloaded meanwhile is refreshed as its day comes near.
      const unknown =
        !since &&
        (await run(db, 'responses', 'readonly', (store) => store.count())) > 0;
      if (unknown || (since && (summary.all || summary.dates?.length))) {
        invalidations = fold([
          ...invalidations,
          {
            at: Date.now(),
            all: unknown || Boolean(summary.all),
            urgent: !unknown && Boolean(summary.urgent),
            dates: unknown ? [] : summary.dates || [],
          },
        ]);
        await run(db, 'meta', 'readwrite', (store) =>
          store.put(invalidations, 'invalidations')
        );
      }
      if (typeof summary.version === 'number') {
        await run(db, 'meta', 'readwrite', (store) =>
          store.put(summary.version, 'contentVersion')
        );
      }
    }
  } catch {
    // Try the downloads anyway.
  }

  const today = isoToday();
  const tomorrow = isoToday(1);
  let fetched = 0;
  // What was stored, for the open pages' lists (cacheAdapter.js summaryOf).
  const stored = [];
  for (const task of plan.tasks) {
    if (fetched >= BACKGROUND_LIMIT) break;
    if (task.date && task.kind !== 'month' && task.date < today) continue;
    const record = await run(db, 'responses', 'readonly', (store) =>
      store.get(task.key)
    );
    if (record && record.schema === SCHEMA) {
      const stale = staleness(record, invalidations);
      if (!stale) continue;
      if (stale === 'soft' && (!task.date || task.date > tomorrow)) continue;
    }
    try {
      // When it was asked for: a change noted meanwhile may not be in it.
      const askedAt = Date.now();
      const response = await fetch(task.url, {
        headers: { 'X-Offline-Sync': '1' },
      });
      if (!response.ok) continue;
      const text = await response.text();
      const data = JSON.parse(text);
      const summary = {
        key: task.key,
        fetchedAt: askedAt,
        schema: SCHEMA,
        kind: task.kind,
        date: task.date,
        profile: task.profile ?? null,
        bytes: text.length,
      };
      await run(db, 'responses', 'readwrite', (store) =>
        store.put({ ...summary, url: task.url, data })
      );
      stored.push(summary);
      fetched += 1;
    } catch {
      // Offline again, or a bad answer: the next run tries again.
      break;
    }
  }
  await run(db, 'meta', 'readwrite', (store) =>
    store.put(Date.now(), 'backgroundSyncAt')
  );
  const windows = await clients.matchAll({ type: 'window' });
  windows.forEach((client) =>
    client.postMessage({ type: 'OFFLINE_BACKGROUND_SYNCED', fetched, stored })
  );
}

// Not while an open page is syncing (they share its lock, sync.js): both
// would download the same plan.
function refreshUnlessSyncing() {
  if (!self.navigator?.locks?.request) return backgroundRefresh();
  return self.navigator.locks.request(
    'dailyoffice-offline-sync',
    { ifAvailable: true },
    (lock) => (lock ? backgroundRefresh() : null)
  );
}

self.addEventListener('periodicsync', (event) => {
  if (event.tag === SYNC_TAG) event.waitUntil(refreshUnlessSyncing());
});

self.addEventListener('sync', (event) => {
  if (event.tag === SYNC_TAG) event.waitUntil(refreshUnlessSyncing());
});
