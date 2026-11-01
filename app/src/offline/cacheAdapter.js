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
    the network and are stored.

  Answers from storage carry `response.offline = { fetchedAt, stale }`.
  Offline with nothing stored, the request fails with `error.isOffline`.
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

const listeners = new Set();

// Called with (key, record) whenever a stored answer changes.
export function onStored(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function headerValue(headers, name) {
  if (!headers) return undefined;
  if (typeof headers.get === 'function') return headers.get(name);
  const lower = name.toLowerCase();
  const key = Object.keys(headers).find((k) => k.toLowerCase() === lower);
  return key ? headers[key] : undefined;
}

export function offlineError(config) {
  const error = new Error('You are offline and this has not been downloaded.');
  error.isOffline = true;
  error.code = 'ERR_OFFLINE';
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

// `fetchedAt` is when the answer was downloaded, when that was earlier (the
// apps' background downloads, native.js).
export async function storeEntry(key, info, url, data, { fetchedAt } = {}) {
  const previous = await readEntry(key);
  const bytes = sizeOf(data);
  const record = {
    key,
    url,
    data,
    kind: info.kind,
    date: info.date,
    profile: info.profile,
    fetchedAt: fetchedAt || Date.now(),
    bytes,
    schema: SCHEMA,
  };
  try {
    await db.put('responses', record);
  } catch {
    // Storage full: the page still gets its answer.
    return null;
  }
  const changed = !previous || previous.bytes !== bytes;
  listeners.forEach((listener) => {
    try {
      listener(key, record, changed);
    } catch {
      // Listeners look after themselves.
    }
  });
  return record;
}

// Store a network answer worth keeping.
async function keep(key, info, url, response) {
  const data = bodyOf(response);
  if (storable(info, response, data)) {
    await storeEntry(key, info, url, data);
  }
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

// Background downloads (`quiet`) never decide that the app is offline on
// their own: only the pages' requests do.
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
  const promise = callNetwork(networkAdapter, config)
    .then(async (response) => {
      await keep(key, info, url, response);
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
  if (method !== 'get') return callNetwork(networkAdapter, config);

  const parsed = parseApiUrl(config.url, config.params);
  const info = parsed && describe(parsed.path, parsed.query);
  if (!info) return callNetwork(networkAdapter, config);

  const key = keyFor(parsed.path, parsed.query);
  const url = absoluteUrl(config);
  const isSync = Boolean(headerValue(config.headers, SYNC_HEADER));

  if (isSync) {
    const response = await callNetwork(networkAdapter, config, { quiet: true });
    await keep(key, info, url, response);
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
    throw offlineError(config);
  }

  if (info.policy === 'cache-first' && stored && !stored.stale) {
    const age = Date.now() - stored.fetchedAt;
    if (info.kind === 'office' || age > (REFRESH_AFTER_MS[info.kind] || 0)) {
      refreshBehind(networkAdapter, config, key, info, url, parsed.query);
    }
    return fromStorage(stored, config);
  }

  const request = callNetwork(networkAdapter, config).then(async (response) => {
    await keep(key, info, url, response);
    return response;
  });

  if (!stored) return request;

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
    if (isNetworkFailure(error)) {
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
