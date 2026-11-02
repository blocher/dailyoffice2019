/*
  Offline-aware requests
  ======================
  Every page asks the API through axios (this.$http). This adapter sits under
  axios, so pages need no changes to work offline:

  - Offices, readings and calendar days are "cache-first": a stored, current
    copy answers at once, and the page's request still goes out behind it to
    refresh the copy (that request is also what counts the view, see
    analytics/middleware.py). Offline, the stored copy answers and the view
    is queued (viewQueue.js).
  - Everything else is "network-first": the API answers when it can; a
    stored copy answers when it can't, or when it is slow to.
  - Requests the sync engine makes carry X-Offline-Sync; they always go to
    the network and are stored. The header is a marker for this adapter
    only and is removed before the request goes out: a custom header would
    cost a CORS preflight that Cloudflare can't cache.

  Answers from storage carry `response.offline = { fetchedAt, stale }`.
  Offline with nothing stored (or when the connection fails and nothing is
  stored), the request fails with `error.isOffline`.
*/
import axios from 'axios';
import * as db from './db';
import { describe, keyFor, parseApiUrl } from './keys';
import {
  isNetworkFailure,
  network,
  reportReachable,
  reportUnreachable,
} from './network';
import { loadInvalidations, stalenessOf } from './staleness';
import { noteUse } from './usage';
import { queueView } from './viewQueue';

// Bump when stored answers can no longer be read by this version of the app.
export const SCHEMA = 1;

// Network-first requests with a stored copy wait this long before the copy
// answers (the request carries on and refreshes the copy).
const SLOW_NETWORK_MS = 4000;

// Cache-first copies younger than this skip the background refresh, except
// offices, whose refresh is also the view count.
const REFRESH_AFTER_MS = {
  readings: 6 * 3600 * 1000,
  day: 6 * 3600 * 1000,
};

export const SYNC_HEADER = 'X-Offline-Sync';

function headerValue(headers, name) {
  if (!headers) return undefined;
  if (typeof headers.get === 'function') return headers.get(name);
  const lower = name.toLowerCase();
  const key = Object.keys(headers).find((k) => k.toLowerCase() === lower);
  return key ? headers[key] : undefined;
}

function removeHeader(headers, name) {
  if (!headers) return;
  if (typeof headers.delete === 'function') {
    headers.delete(name);
    return;
  }
  const lower = name.toLowerCase();
  Object.keys(headers)
    .filter((k) => k.toLowerCase() === lower)
    .forEach((k) => delete headers[k]);
}

export function offlineError(config, cause) {
  const error = new Error('You are offline and this has not been downloaded.');
  error.isOffline = true;
  error.code = 'ERR_OFFLINE';
  error.config = config;
  if (cause) error.cause = cause;
  return error;
}

// A sync download that arrived but couldn't be stored (storage is full).
export function notStoredError(config) {
  const error = new Error('There is no room left to store downloads.');
  error.code = 'ERR_NOT_STORED';
  error.config = config;
  return error;
}

function absoluteUrl(config) {
  try {
    const origin =
      typeof window !== 'undefined'
        ? window.location.href
        : 'http://localhost/';
    const url = new window.URL(config.url, origin);
    Object.entries(config.params || {}).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        url.searchParams.set(key, String(value));
      }
    });
    return url.toString();
  } catch {
    return config.url;
  }
}

// Adapters hand back the body before axios parses it.
function bodyOf(response) {
  const data = response?.data;
  if (typeof data !== 'string') return data;
  try {
    return JSON.parse(data);
  } catch {
    return null;
  }
}

// Whether a parsed answer of this kind is worth keeping (also for the apps'
// background downloads, native.js).
export function keepable(kind, data) {
  if (!data || typeof data !== 'object') return false;
  if (kind === 'audio') {
    // Only a finished track; "preparing" answers are asked again later.
    const track = data.audio?.single_track;
    return Array.isArray(track) && track.length > 0;
  }
  return true;
}

function storable(info, response, data) {
  if (!response || response.status !== 200) return false;
  return keepable(info.kind, data);
}

function sizeOf(data) {
  try {
    return JSON.stringify(data).length;
  } catch {
    return 0;
  }
}

/*
  What is stored, without the answers themselves. A sync run checks hundreds
  of keys, and reading each answer whole (often hundreds of KB) just to see
  when it was downloaded is slow on a phone. Filled from storage once, then
  kept in step by storeEntry, removeEntries and clearEntries, which also
  tell the app's other tabs (they share the storage). The service worker's
  writes come in through applyStoredSummaries (pwa.js).
*/
let storedIndex = null;
let indexing = null;
// Bumped by a reset, so a scan that started before it isn't kept.
let indexGeneration = 0;

export function summaryOf(record) {
  const { key, fetchedAt, schema, kind, date, profile, bytes } = record;
  return { key, fetchedAt, schema, kind, date, profile, bytes };
}

function loadStoredIndex() {
  if (storedIndex) return Promise.resolve(storedIndex);
  if (!indexing) {
    const generation = indexGeneration;
    const map = new Map();
    const scan = db
      .eachRecord(
        'responses',
        (record) => {
          map.set(record.key, summaryOf(record));
          return null;
        },
        'readonly'
      )
      .then(() => {
        if (generation === indexGeneration) storedIndex = map;
        return map;
      })
      // Unreadable: answer from what was read, and try again next time.
      .catch(() => map)
      .finally(() => {
        if (indexing === scan) indexing = null;
      });
    indexing = scan;
  }
  return indexing;
}

function updateIndex(change) {
  if (storedIndex) change(storedIndex);
  else if (indexing) indexing.then(change);
}

export function resetStoredIndex() {
  storedIndex = null;
  indexing = null;
  indexGeneration += 1;
}

const channel =
  typeof window !== 'undefined' && typeof window.BroadcastChannel === 'function'
    ? new window.BroadcastChannel('dailyoffice-offline-responses')
    : null;

function tellOtherTabs(message) {
  try {
    channel?.postMessage(message);
  } catch {
    // They find out when they next load.
  }
}

// Answers another writer stored (another tab, the service worker).
export function applyStoredSummaries(summaries) {
  if (!Array.isArray(summaries)) {
    resetStoredIndex();
    return;
  }
  updateIndex((map) =>
    summaries.forEach((summary) => {
      if (summary?.key) map.set(summary.key, summary);
    })
  );
}

if (channel) {
  channel.onmessage = ({ data }) => {
    if (data?.type === 'stored') applyStoredSummaries([data.summary]);
    else if (data?.type === 'removed' && Array.isArray(data.keys))
      updateIndex((map) => data.keys.forEach((key) => map.delete(key)));
    else if (data?.type === 'cleared') resetStoredIndex();
  };
}

// A stored answer's details (not its data), with its staleness; or null.
export async function readStoredInfo(key) {
  try {
    await loadInvalidations();
    const info = (await loadStoredIndex()).get(key);
    if (!info || info.schema !== SCHEMA) return null;
    return { ...info, stale: stalenessOf(info) };
  } catch {
    return null;
  }
}

// Every stored answer's details (for pruning).
export async function storedInfos() {
  return [...(await loadStoredIndex()).values()];
}

export async function removeEntries(keys) {
  if (!keys.length) return;
  await Promise.all(keys.map((key) => db.remove('responses', key)));
  updateIndex((map) => keys.forEach((key) => map.delete(key)));
  tellOtherTabs({ type: 'removed', keys });
}

// Remove every stored answer.
export async function clearEntries() {
  await db.clear('responses');
  resetStoredIndex();
  tellOtherTabs({ type: 'cleared' });
}

export async function readEntry(key) {
  try {
    await loadInvalidations();
    const record = await db.get('responses', key);
    if (!record || record.schema !== SCHEMA) return null;
    record.stale = stalenessOf(record);
    return record;
  } catch {
    return null;
  }
}

// `fetchedAt` is when the answer was asked for (a change noted while it was
// on its way may not be in it), or downloaded in the apps' background
// (native.js); `bytes` its size, when known. Resolves to null when storage
// is full; rejects when storage fails otherwise.
export async function storeEntry(
  key,
  info,
  url,
  data,
  { fetchedAt, bytes } = {}
) {
  const record = {
    key,
    url,
    data,
    kind: info.kind,
    date: info.date,
    profile: info.profile,
    fetchedAt: fetchedAt || Date.now(),
    bytes: bytes || sizeOf(data),
    schema: SCHEMA,
  };
  try {
    await db.put('responses', record);
  } catch (error) {
    if (error?.name !== 'QuotaExceededError') throw error;
    return null;
  }
  const summary = summaryOf(record);
  updateIndex((map) => map.set(key, summary));
  tellOtherTabs({ type: 'stored', summary });
  return record;
}

// Store a network answer worth keeping. Resolves to false when it was worth
// keeping but couldn't be stored.
async function keep(key, info, url, response, fetchedAt) {
  const data = bodyOf(response);
  if (!storable(info, response, data)) return true;
  const record = await storeEntry(key, info, url, data, {
    fetchedAt,
    bytes: typeof response.data === 'string' ? response.data.length : 0,
  });
  return Boolean(record);
}

function fromStorage(record, config) {
  return {
    data: record.data,
    status: 200,
    statusText: 'OK',
    headers: { 'x-offline': 'storage' },
    config,
    request: null,
    offline: { fetchedAt: record.fetchedAt, stale: Boolean(record.stale) },
  };
}

let recentFailures = [];

function noteFailure(error) {
  // One failed request can be a fluke; a connection error, or two failures
  // within 20 seconds, means the API can't be reached.
  const now = Date.now();
  recentFailures = recentFailures.filter((t) => now - t < 20000);
  recentFailures.push(now);
  if (error?.code === 'ERR_NETWORK' || recentFailures.length >= 2) {
    reportUnreachable();
  }
}

// Only the pages' reads of what is stored decide that the app is offline:
// background downloads, writes and other requests are `quiet` (a blocked
// analytics post isn't a lost connection).
async function callNetwork(networkAdapter, config, { quiet = false } = {}) {
  try {
    const response = await networkAdapter(config);
    recentFailures = [];
    reportReachable();
    return response;
  } catch (error) {
    if (error?.response) {
      reportReachable();
    } else if (!quiet && isNetworkFailure(error)) {
      noteFailure(error);
    }
    throw error;
  }
}

const refreshing = new Map();

function refreshBehind(networkAdapter, config, key, info, url, query) {
  if (refreshing.has(key)) return refreshing.get(key);
  const askedAt = Date.now();
  const promise = callNetwork(networkAdapter, config)
    .then(async (response) => {
      // Not storing it isn't a lost connection (below).
      await keep(key, info, url, response, askedAt).catch(() => {});
    })
    .catch((error) => {
      // The view still happened; count it once the app is online again.
      if (info.kind === 'office' && isNetworkFailure(error)) {
        queueView(info, query);
      }
    })
    .finally(() => refreshing.delete(key));
  refreshing.set(key, promise);
  return promise;
}

function delay(ms) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

export async function handle(config, networkAdapter) {
  const method = (config.method || 'get').toLowerCase();
  if (method !== 'get') {
    return callNetwork(networkAdapter, config, { quiet: true });
  }

  const parsed = parseApiUrl(config.url, config.params);
  const info = parsed && describe(parsed.path, parsed.query);
  if (!info) return callNetwork(networkAdapter, config, { quiet: true });

  const key = keyFor(parsed.path, parsed.query);
  const url = absoluteUrl(config);
  const isSync = Boolean(headerValue(config.headers, SYNC_HEADER));

  if (isSync) {
    removeHeader(config.headers, SYNC_HEADER);
    const askedAt = Date.now();
    const response = await callNetwork(networkAdapter, config, { quiet: true });
    if (!(await keep(key, info, url, response, askedAt))) {
      throw notStoredError(config);
    }
    return response;
  }

  if (info.kind === 'office') noteUse(info.serviceType);
  if (info.kind === 'readings') noteUse('readings');

  const stored = await readEntry(key);

  if (!network.online) {
    if (stored) {
      if (info.kind === 'office') queueView(info, parsed.query);
      return fromStorage(stored, config);
    }
    // Requests have been failing, but the browser has a network: one more
    // try rather than "offline" for a request that may well get through
    // (iOS cuts requests off when the app goes to the background).
    if (!network.browserOnline) throw offlineError(config);
  }

  if (info.policy === 'cache-first' && stored && !stored.stale) {
    const age = Date.now() - stored.fetchedAt;
    if (info.kind === 'office' || age > (REFRESH_AFTER_MS[info.kind] || 0)) {
      refreshBehind(networkAdapter, config, key, info, url, parsed.query);
    }
    return fromStorage(stored, config);
  }

  // The page has its answer before it is saved.
  const askedAt = Date.now();
  const request = callNetwork(networkAdapter, config).then((response) => {
    keep(key, info, url, response, askedAt).catch(() => {});
    return response;
  });

  if (!stored) {
    // The failure took the app offline (no connection) and nothing is
    // stored: the page says so as it would offline (OfflineMiss), rather
    // than show a bare error. A one-off failure (a timeout) stays an error.
    return request.catch((error) => {
      throw isNetworkFailure(error) && !network.online
        ? offlineError(config, error)
        : error;
    });
  }

  // A stored copy is waiting: the network gets a few seconds, then the copy
  // answers (and the request still refreshes it when it lands).
  const slow = Symbol('slow');
  try {
    const winner = await Promise.race([
      request,
      delay(SLOW_NETWORK_MS).then(() => slow),
    ]);
    if (winner !== slow) return winner;
    request.catch(() => {});
    return fromStorage(stored, config);
  } catch (error) {
    // No connection, or the API is down (a 502 during a deploy): the stored
    // copy is better than an error.
    if (isNetworkFailure(error) || error?.response?.status >= 500) {
      if (info.kind === 'office') queueView(info, parsed.query);
      return fromStorage(stored, config);
    }
    throw error;
  }
}

export function installCacheAdapter(instance = axios) {
  const networkAdapter = axios.getAdapter(instance.defaults.adapter);
  instance.defaults.adapter = (config) => handle(config, networkAdapter);
}
