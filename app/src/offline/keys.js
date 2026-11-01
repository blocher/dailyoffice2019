/*
  Which API requests are kept offline, and under what key
  =======================================================
  A request's key is its API path plus its query parameters in sorted order,
  so the same office asked for by a page and by the sync engine is stored
  once, whatever order the parameters were written in.
*/

export const API_PREFIX = 'api/v1/';

// Settings-independent parameters: everything else in an office or readings
// query is a setting, and together they make the request's "profile".
const NON_SETTING_PARAMS = new Set([
  'extra_collects',
  'include_audio_links',
  'translation',
  'psalms',
  'style',
  'reload',
]);

// Never stored: live or write-only endpoints, and big media.
const UNCACHED = [
  /^analytics\//,
  /^content_changes/,
  /^audio_track\//,
  /^calendar\/feed\//,
  /^email_signup/,
  /^podcasts\/custom/,
  /^readings_audio\//,
  /^api-auth\//,
  /^audio$/,
];

function apiBase() {
  return import.meta.env.VITE_API_URL || '/';
}

// The part of a URL after /api/v1/, split into path and parameters; null
// for anything that isn't this app's API.
export function parseApiUrl(url, params = null) {
  if (!url) return null;
  let parsed;
  try {
    const origin =
      typeof window !== 'undefined'
        ? window.location.href
        : 'http://localhost/';
    parsed = new window.URL(url, new window.URL(apiBase(), origin));
  } catch {
    return null;
  }
  const marker = `/${API_PREFIX}`;
  const index = parsed.pathname.indexOf(marker);
  if (index === -1) return null;
  let base;
  try {
    const origin =
      typeof window !== 'undefined'
        ? window.location.href
        : 'http://localhost/';
    base = new window.URL(apiBase(), origin);
  } catch {
    base = null;
  }
  if (base && parsed.origin !== base.origin) return null;
  const path = parsed.pathname.slice(index + marker.length).replace(/\/+$/, '');
  const query = {};
  parsed.searchParams.forEach((value, key) => {
    query[key] = value;
  });
  if (params && typeof params === 'object') {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) query[key] = String(value);
    });
  }
  return { path, query };
}

export function keyFor(path, query) {
  const parts = Object.keys(query)
    .filter((key) => key !== 'reload')
    .sort()
    .map((key) => `${key}=${query[key]}`);
  return parts.length ? `${path}?${parts.join('&')}` : path;
}

// FNV-1a: a short, stable name for a combination of settings.
export function hashString(value) {
  let hash = 0x811c9dc5;
  for (let i = 0; i < value.length; i += 1) {
    hash ^= value.charCodeAt(i);
    hash = Math.imul(hash, 0x01000193);
  }
  return (hash >>> 0).toString(36);
}

export function profileFor(query) {
  const settings = Object.keys(query)
    .filter((key) => !NON_SETTING_PARAMS.has(key))
    .sort()
    .map((key) => `${key}=${query[key]}`)
    .join('&');
  return settings ? hashString(settings) : null;
}

export function profileForSettings(settings) {
  const query = {};
  Object.entries(settings || {}).forEach(([key, value]) => {
    query[key] = String(value);
  });
  if (!query.bible_translation) query.bible_translation = 'esv';
  return profileFor(query);
}

export function isoDate(year, month, day) {
  const pad = (n) => String(n).padStart(2, '0');
  return `${year}-${pad(month)}-${pad(day)}`;
}

function dateFrom(match) {
  return isoDate(Number(match[1]), Number(match[2]), Number(match[3]));
}

/*
  What a request is, for storage:
    kind     office | audio | readings | day | month | reference | messages
    date     the day it is for (YYYY-MM-DD), when it is for one day
    profile  the settings it was asked for with (offices and readings)
    policy   'cache-first'   answer from storage when fresh, refresh behind
             'network-first' ask the network, fall back to storage
  null when the request is not kept.
*/
export function describe(path, query) {
  if (UNCACHED.some((pattern) => pattern.test(path))) return null;
  let match = path.match(
    /^(office|family)\/([a-z_]+)\/(\d{4})-(\d{1,2})-(\d{1,2})$/
  );
  if (match) {
    const audio = Boolean(query.include_audio_links);
    return {
      kind: audio ? 'audio' : 'office',
      date: isoDate(Number(match[3]), Number(match[4]), Number(match[5])),
      profile: profileFor(query),
      serviceType: match[1],
      office: match[2],
      policy: audio ? 'network-first' : 'cache-first',
    };
  }
  match = path.match(/^readings\/(\d{4})-(\d{1,2})-(\d{1,2})$/);
  if (match) {
    return {
      kind: 'readings',
      date: dateFrom(match),
      profile: profileFor(query),
      policy: 'cache-first',
    };
  }
  match = path.match(/^calendar\/(\d{4})-(\d{1,2})-(\d{1,2})$/);
  if (match) {
    return {
      kind: 'day',
      date: dateFrom(match),
      profile: null,
      policy: 'cache-first',
    };
  }
  match = path.match(/^calendar\/(\d{4})-(\d{1,2})$/);
  if (match) {
    return {
      kind: 'month',
      date: isoDate(Number(match[1]), Number(match[2]), 1),
      profile: null,
      policy: 'network-first',
    };
  }
  if (/^site_messages/.test(path)) {
    return {
      kind: 'messages',
      date: null,
      profile: null,
      policy: 'network-first',
    };
  }
  return {
    kind: 'reference',
    date: null,
    profile: null,
    policy: 'network-first',
  };
}
