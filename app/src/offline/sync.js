/*
  The sync engine
  ===============
  Keeps the next days of offices on the device, for the reader's own
  settings, so the app works offline without anyone thinking about it.

  A run:
    1. reports office views prayed offline (viewQueue.js);
    2. asks the API what content changed since the last run
       (/api/v1/content_changes, see staleness.js);
    3. plans what should be stored: today and the days ahead (the number of
       days is an offline preference), each with the daily offices, Family
       Prayer and the Readings page when they are used, the calendar day,
       the calendar months, and the reference pages (the settings list, the
       Psalter, collects, the Great Litany);
    4. downloads what is missing or out of date, most needed first: the
       office for this time of day, then the rest of today, tomorrow, and on;
    5. downloads audio for today and tomorrow when asked to (audio.js);
    6. removes what is no longer needed: past days and other settings.

  Runs start when the app opens or comes back to the front, when the
  connection returns, when settings change, after midnight, and from the
  Offline panel. Downloads carry X-Offline-Sync so the API doesn't count
  them as views.

  The plan is also written to storage for the service worker, which follows
  it in the background where the browser allows (public/sw.js). In the iOS
  and Android apps it goes to the OfflineSync plugin instead, whose
  background task downloads into an inbox the app empties into storage the
  next time it opens (native.js).
*/
import axios from 'axios';
import { reactive } from 'vue';
import * as db from './db';
import {
  SCHEMA,
  SYNC_HEADER,
  readEntry,
  readStoredInfo,
  removeEntries,
  resetStoredIndex,
  storedInfos,
} from './cacheAdapter';
import {
  describe,
  isoDate,
  keyFor,
  parseApiUrl,
  profileForSettings,
} from './keys';
import { network } from './network';
import { AUDIO_DAYS, effectiveDays, offlinePrefs } from './preferences';
import {
  addInvalidation,
  loadInvalidations,
  reloadInvalidations,
  stalenessOf,
  trimInvalidations,
} from './staleness';
import { usedRecently } from './usage';
import { flushViews } from './viewQueue';
import {
  DAILY_OFFICES,
  apiUrl,
  dayUrl,
  monthUrl,
  officeUrl,
  readingsUrl,
} from './urls';
import {
  audioSummary,
  hasTrack,
  pruneTracks,
  saveTrack,
  trackKey,
} from './audio';
import { resolveAudioUrl } from '@/helpers/officeAudio';
import { scheduleBackground } from './native';

const CONCURRENCY = 2;
const REQUEST_TIMEOUT_MS = 45000;
// Soft-stale reference pages are refreshed at most this often.
const REFERENCE_REFRESH_MS = 7 * 24 * 3600 * 1000;
// Past days kept (yesterday's office stays a tap away).
const KEEP_PAST_DAYS = 1;
// Days a page opened outside the window is kept.
const KEEP_VISITED_MS = 14 * 24 * 3600 * 1000;
const RECHECK_AFTER_MS = 10 * 60 * 1000;
const AUDIO_RETRY_MS = 3 * 60 * 1000;

const REFERENCE_PATHS = [
  'available_settings/',
  'litany',
  'grouped_collects',
  'psalms',
  'psalms/topics/',
  'about',
];

export const syncState = reactive({
  // idle | checking | syncing | done | offline | error | off | unavailable
  // (this browser can't keep anything: a private window, blocked site data)
  status: 'idle',
  reason: '',
  done: 0,
  total: 0,
  current: '',
  readyThrough: null,
  readyDays: 0,
  plannedDays: 0,
  lastSyncAt: null,
  lastCheckAt: null,
  failed: 0,
  storageBytes: 0,
  audio: { wanted: 0, ready: 0, preparing: 0, bytes: 0, active: false },
  error: null,
});

let contextProvider = async () => null;
let runId = 0;
let running = null;
let queued = null;
let audioRetryTimer = null;

export function configureSync({ getContext }) {
  contextProvider = getContext;
}

function startOfDay(date) {
  const copy = new Date(date);
  copy.setHours(0, 0, 0, 0);
  return copy;
}

function addDays(date, days) {
  const copy = new Date(date);
  copy.setDate(copy.getDate() + days);
  return copy;
}

function isoOf(date) {
  return isoDate(date.getFullYear(), date.getMonth() + 1, date.getDate());
}

// The office one is most likely to pray next, given the hour.
export function officeOrderFor(hour) {
  const start = hour < 11 ? 0 : hour < 14 ? 1 : hour < 19 ? 2 : 3;
  return [...DAILY_OFFICES.slice(start), ...DAILY_OFFICES.slice(0, start)];
}

const FAMILY_FOR_DAILY = {
  morning_prayer: 'morning_prayer',
  midday_prayer: 'midday_prayer',
  evening_prayer: 'early_evening_prayer',
  compline: 'close_of_day_prayer',
};

function task(url, priority, label) {
  const parsed = parseApiUrl(url);
  const info = parsed && describe(parsed.path, parsed.query);
  if (!info) return null;
  return {
    url,
    key: keyFor(parsed.path, parsed.query),
    kind: info.kind,
    date: info.date,
    profile: info.profile,
    serviceType: info.serviceType,
    office: info.office,
    priority,
    label,
  };
}

/*
  Everything that should be stored, most needed first. Pure, for testing:
  `now` is the current time; `context` the reader's settings.
*/
export function buildPlan({
  now = new Date(),
  days,
  settings,
  extraCollects = null,
  family = false,
  readings = null,
}) {
  const tasks = [];
  if (!settings || days <= 0) return tasks;
  const today = startOfDay(now);
  const order = officeOrderFor(now.getHours());
  const longDay = (date) =>
    date.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
    });

  const add = (url, priority, label) => {
    const item = task(url, priority, label);
    if (item && !tasks.some((t) => t.key === item.key)) tasks.push(item);
  };

  // The settings list first: without it the app can't start offline.
  add(apiUrl('available_settings/'), 0, 'Settings');

  const months = new Set();
  for (let offset = 0; offset < days; offset += 1) {
    const date = addDays(today, offset);
    const base = 10 + offset * 10;
    const when =
      offset === 0 ? 'today' : offset === 1 ? 'tomorrow' : longDay(date);
    order.forEach((office, index) => {
      add(
        officeUrl({
          serviceType: 'office',
          office,
          date,
          settings,
          extraCollects,
        }),
        base + index * 0.1,
        `${office.replace(/_/g, ' ')}, ${when}`
      );
    });
    if (family) {
      order.forEach((office, index) => {
        add(
          officeUrl({
            serviceType: 'family',
            office: FAMILY_FOR_DAILY[office],
            date,
            settings,
            extraCollects,
          }),
          base + 1 + index * 0.1,
          `Family Prayer, ${when}`
        );
      });
    }
    add(dayUrl(date), base + 2, `Calendar, ${when}`);
    if (readings && offset < 14) {
      add(
        readingsUrl({ date, settings, ...readings }),
        base + 3,
        `Readings, ${when}`
      );
    }
    months.add(`${date.getFullYear()}-${date.getMonth() + 1}`);
  }
  [...months].forEach((ym, index) => {
    const [year, month] = ym.split('-').map(Number);
    add(monthUrl(year, month), 25 + index * 10, 'Calendar month');
  });
  // The library, once the next few days are in.
  REFERENCE_PATHS.slice(1).forEach((path, index) => {
    add(apiUrl(path), 75 + index, 'The library');
  });
  return tasks.sort((a, b) => a.priority - b.priority);
}

function needsDownload(record, item, todayIso, tomorrowIso) {
  if (!record) return true;
  const stale = stalenessOf(record);
  if (!stale) return false;
  if (stale === 'hard') return true;
  if (!item.date) return Date.now() - record.fetchedAt > REFERENCE_REFRESH_MS;
  if (item.kind === 'month')
    return item.date.slice(0, 7) === todayIso.slice(0, 7);
  return item.date <= tomorrowIso;
}

async function checkContentChanges() {
  const since = (await db.meta.get('contentVersion')) || 0;
  const { data } = await axios.get(apiUrl('content_changes'), {
    params: { since },
    timeout: 15000,
  });
  if (!data || typeof data.version !== 'number') return;
  if (since) await addInvalidation(data);
  await db.meta.set('contentVersion', data.version);
}

async function download(item) {
  try {
    await axios.get(item.url, {
      headers: { [SYNC_HEADER]: '1' },
      timeout: REQUEST_TIMEOUT_MS,
    });
    return true;
  } catch (error) {
    // Not there (a date outside the calendar): nothing to keep.
    return error?.response?.status === 404;
  }
}

async function runQueue(items, current, onDone) {
  let index = 0;
  const worker = async () => {
    while (index < items.length && current === runId && network.online) {
      const item = items[index];
      index += 1;
      syncState.current = item.label;
      const ok = await download(item);
      onDone(item, ok);
    }
  };
  await Promise.all(Array.from({ length: CONCURRENCY }, worker));
}

function audioWanted(settings) {
  const translation = settings?.bible_translation || 'esv';
  const language = settings?.display_language || 'english';
  return (
    offlinePrefs.audio &&
    ['esv', 'kjv'].includes(translation) &&
    language === 'english' &&
    offlinePrefs.audioOffices.length > 0
  );
}

// The offices whose audio is wanted, for `count` days from today.
function audioItems(context, today, count) {
  const items = [];
  if (!audioWanted(context.settings) || effectiveDays() === 0) return items;
  for (let offset = 0; offset < count; offset += 1) {
    const date = addDays(today, offset);
    offlinePrefs.audioOffices.forEach((office) => {
      items.push({
        date,
        office,
        url:
          officeUrl({
            serviceType: 'office',
            office,
            date,
            settings: context.settings,
            extraCollects: context.extraCollects,
          }) + '&include_audio_links=true',
      });
    });
  }
  return items;
}

const slotOf = (date, office) => `${date}|${office}`;

async function syncAudio(context, current, today) {
  const keep = new Set();
  // Offices whose track couldn't be worked out this run (still being
  // prepared, or the request failed): whatever is stored for them stays.
  const unresolved = new Set();
  let finished = true;
  const state = syncState.audio;
  state.preparing = 0;
  state.ready = 0;
  const items = audioItems(context, today, AUDIO_DAYS);
  state.wanted = items.length;
  state.active = items.length > 0;
  for (const item of items) {
    if (current !== runId || !network.online) {
      finished = false;
      break;
    }
    const slot = slotOf(isoOf(item.date), item.office);
    let track = null;
    try {
      const parsed = parseApiUrl(item.url);
      const stored = await readEntry(keyFor(parsed.path, parsed.query));
      let data = stored && !stalenessOf(stored) ? stored.data : null;
      if (!data) {
        syncState.current = `Audio: ${item.office.replace(/_/g, ' ')}`;
        const response = await axios.get(item.url, {
          headers: { [SYNC_HEADER]: '1' },
          timeout: REQUEST_TIMEOUT_MS,
        });
        data = response.data;
      }
      if (data?.audio?.status === 'preparing') {
        state.preparing += 1;
        unresolved.add(slot);
        continue;
      }
      const raw = data?.audio?.single_track?.[0];
      if (!raw) continue;
      track = trackKey(resolveAudioUrl(raw));
      keep.add(track);
      if (!(await hasTrack(track))) {
        syncState.current = `Audio: ${item.office.replace(/_/g, ' ')}`;
        await saveTrack(track, { date: isoOf(item.date), office: item.office });
      }
      state.ready += 1;
    } catch {
      // Try again on the next run.
      if (!track) unresolved.add(slot);
    }
  }
  const summary = await audioSummary();
  // A run cut short hasn't seen every office: removing tracks now would drop
  // the ones it didn't reach (going offline mid-run would empty the audio).
  if (finished) {
    summary.tracks
      .filter((record) => unresolved.has(slotOf(record.date, record.office)))
      .forEach((record) => keep.add(record.url));
    await pruneTracks(keep);
    state.bytes = (await audioSummary()).bytes;
  } else {
    state.bytes = summary.bytes;
  }
  state.active = false;
  if (state.preparing && current === runId) scheduleAudioRetry();
}

function scheduleAudioRetry() {
  if (audioRetryTimer || typeof window === 'undefined') return;
  audioRetryTimer = window.setTimeout(() => {
    audioRetryTimer = null;
    requestSync('audio');
  }, AUDIO_RETRY_MS);
}

/*
  Remove what the plan no longer needs. Returns the bytes kept and the
  oldest download time (for trimming the change list).
*/
async function prune(planKeys, keepProfiles, today, days) {
  const oldest = isoOf(addDays(today, -KEEP_PAST_DAYS));
  const windowEnd = isoOf(addDays(today, Math.max(days, 1) + 1));
  const now = Date.now();
  let bytes = 0;
  let oldestFetched = now;
  const dropped = [];
  for (const record of await storedInfos()) {
    const drop =
      !planKeys.has(record.key) &&
      (record.schema !== SCHEMA ||
        (record.date && record.kind !== 'month' && record.date < oldest) ||
        (record.kind === 'month' &&
          record.date.slice(0, 7) < oldest.slice(0, 7)) ||
        (record.profile && !keepProfiles.includes(record.profile)) ||
        (record.kind === 'audio' && record.date > windowEnd) ||
        (record.date &&
          record.date > windowEnd &&
          now - record.fetchedAt > KEEP_VISITED_MS) ||
        (record.kind === 'reference' &&
          now - record.fetchedAt > 60 * 24 * 3600 * 1000));
    if (drop) {
      dropped.push(record.key);
    } else {
      bytes += record.bytes || 0;
      oldestFetched = Math.min(oldestFetched, record.fetchedAt);
    }
  }
  await removeEntries(dropped);
  return { bytes, oldestFetched };
}

// The current settings and the ones before them stay downloaded, so going
// back to them works offline.
async function rememberProfile(profile) {
  const stored = (await db.meta.get('profiles')) || [];
  const profiles = [profile, ...stored.filter((p) => p !== profile)].slice(
    0,
    2
  );
  await db.meta.set('profiles', profiles);
  return profiles;
}

/*
  Whether today's offices are stored for these settings: offline, the
  Settings page offers only choices that would still have something to pray.
*/
export async function canPrayOfflineWith(settings, extraCollects = null) {
  const now = new Date();
  const today = startOfDay(now);
  const office = officeOrderFor(now.getHours())[0];
  const url = officeUrl({
    serviceType: 'office',
    office,
    date: today,
    settings,
    extraCollects,
  });
  const parsed = parseApiUrl(url);
  if (!parsed) return false;
  return Boolean(await readStoredInfo(keyFor(parsed.path, parsed.query)));
}

// How far ahead every planned office is stored, from today.
async function measureReadiness(plan, today, days) {
  const byDate = new Map();
  plan
    .filter((item) => item.kind === 'office')
    .forEach((item) => {
      if (!byDate.has(item.date)) byDate.set(item.date, []);
      byDate.get(item.date).push(item);
    });
  let readyDays = 0;
  let readyThrough = null;
  for (let offset = 0; offset < days; offset += 1) {
    const iso = isoOf(addDays(today, offset));
    const items = byDate.get(iso) || [];
    if (!items.length) break;
    const records = await Promise.all(
      items.map((item) => readStoredInfo(item.key))
    );
    if (records.some((record) => !record || record.stale === 'hard')) break;
    readyDays += 1;
    readyThrough = iso;
  }
  syncState.readyDays = readyDays;
  syncState.readyThrough = readyThrough;
}

// How far ahead every planned office is stored, after downloads arrived
// from outside a run (the apps' background downloads, native.js).
export async function refreshReadiness() {
  const plan = await db.meta.get('plan');
  if (!plan?.tasks) return;
  await loadInvalidations();
  await measureReadiness(plan.tasks, startOfDay(new Date()), plan.days || 0);
}

async function writeBackgroundPlan(plan, days) {
  // The service worker (and, in the apps, the OfflineSync plugin) follows
  // this list in the background.
  const background = {
    createdAt: Date.now(),
    days,
    apiBase: import.meta.env.VITE_API_URL || '/',
    tasks: plan.map(({ url, key, kind, date, profile, priority }) => ({
      url,
      key,
      kind,
      date,
      profile,
      priority,
    })),
  };
  await db.meta.set('plan', background);
  return background;
}

async function persistStorage() {
  try {
    if (
      navigator.storage?.persisted &&
      !(await navigator.storage.persisted())
    ) {
      await navigator.storage.persist?.();
    }
  } catch {
    // The browser decides.
  }
}

async function runOnce(reason) {
  const current = ++runId;
  syncState.reason = reason;
  syncState.error = null;
  const context = await contextProvider();
  if (!context?.settings) {
    syncState.status = 'idle';
    return;
  }
  // The service worker may have noted changes since the last run.
  await reloadInvalidations();
  const days = effectiveDays();
  const now = new Date();
  const today = startOfDay(now);
  const plan = buildPlan({
    now,
    days,
    settings: context.settings,
    extraCollects: context.extraCollects,
    family:
      offlinePrefs.family === 'on' ||
      (offlinePrefs.family === 'auto' && (await usedRecently('family'))),
    readings: (await usedRecently('readings')) ? context.readings : null,
  });
  syncState.plannedDays = days;

  // Nowhere to keep downloads: they would be lost on reload, so spend no
  // data on them.
  await db.openDb();
  if (!db.isPersistent()) {
    syncState.status = days === 0 ? 'off' : 'unavailable';
    return;
  }

  if (!network.online) {
    syncState.status = days === 0 ? 'off' : 'offline';
    await measureReadiness(plan, today, days);
    return;
  }

  syncState.status = 'checking';
  flushViews();
  try {
    await checkContentChanges();
  } catch {
    // The changes wait for the next run; downloads can still go ahead.
  }
  syncState.lastCheckAt = Date.now();
  if (current !== runId) return;

  const todayIso = isoOf(today);
  const tomorrowIso = isoOf(addDays(today, 1));
  const records = await Promise.all(
    plan.map((item) => readStoredInfo(item.key))
  );
  const missing = plan.filter((item, i) =>
    needsDownload(records[i], item, todayIso, tomorrowIso)
  );

  syncState.total = missing.length;
  syncState.done = 0;
  syncState.failed = 0;
  if (missing.length) {
    syncState.status = 'syncing';
    await runQueue(missing, current, (item, ok) => {
      if (current !== runId) return;
      syncState.done += 1;
      if (!ok) syncState.failed += 1;
    });
  }
  if (current !== runId) return;

  await syncAudio(context, current, today);
  if (current !== runId) return;

  const profile = profileForSettings(context.settings);
  const keepProfiles = await rememberProfile(profile);
  const planKeys = new Set(plan.map((item) => item.key));
  const { bytes, oldestFetched } = await prune(
    planKeys,
    keepProfiles,
    today,
    days
  );
  await trimInvalidations(oldestFetched);
  syncState.storageBytes = bytes;
  await measureReadiness(plan, today, days);
  const background = await writeBackgroundPlan(plan, days);
  // Days after today count too: a background run tomorrow wants tomorrow's.
  await scheduleBackground(background, {
    audio: audioItems(context, today, AUDIO_DAYS + 2).map((item) => ({
      url: item.url,
      date: isoOf(item.date),
      office: item.office,
    })),
  });
  if (days > 0) persistStorage();

  syncState.current = '';
  syncState.lastSyncAt = Date.now();
  await db.meta.set('lastSyncAt', syncState.lastSyncAt);
  syncState.status =
    days === 0
      ? 'off'
      : !network.online
        ? 'offline'
        : syncState.failed
          ? 'error'
          : 'done';
  if (syncState.failed) {
    syncState.error = `${syncState.failed} download${syncState.failed === 1 ? '' : 's'} didn’t finish. They’ll be tried again.`;
  }
}

// Only one tab syncs at a time.
function withSyncLock(run) {
  if (typeof navigator !== 'undefined' && navigator.locks?.request) {
    return navigator.locks.request(
      'dailyoffice-offline-sync',
      { ifAvailable: true },
      (lock) => (lock ? run() : undefined)
    );
  }
  return run();
}

/*
  Start a run, or note that another is wanted once this one ends. A run
  for new settings or preferences replaces the one going.
*/
export function requestSync(reason = 'manual') {
  if (running) {
    if (['settings', 'preferences', 'manual'].includes(reason)) {
      runId += 1; // ends the current run at its next step
    }
    queued = reason;
    return running;
  }
  running = withSyncLock(() => runOnce(reason))
    .catch((error) => {
      syncState.status = 'error';
      syncState.error =
        'Downloads stopped unexpectedly. They’ll be tried again.';
      // eslint-disable-next-line no-console
      console.warn('Offline sync failed', error);
    })
    .finally(() => {
      running = null;
      if (queued) {
        const next = queued;
        queued = null;
        requestSync(next);
      }
    });
  return running;
}

export function isSyncing() {
  return Boolean(running);
}

export function syncIfDue(reason) {
  const last = syncState.lastCheckAt || 0;
  if (Date.now() - last > RECHECK_AFTER_MS) requestSync(reason);
}

export async function loadSyncStatus() {
  syncState.lastSyncAt = (await db.meta.get('lastSyncAt')) || null;
}

// Remove every download (the Offline panel's "Remove downloads").
export async function clearDownloads() {
  runId += 1;
  await db.clear('responses');
  resetStoredIndex();
  await pruneTracks(new Set());
  await db.meta.set('plan', null);
  await scheduleBackground(null);
  syncState.storageBytes = 0;
  syncState.readyDays = 0;
  syncState.readyThrough = null;
  syncState.audio.bytes = 0;
  syncState.audio.ready = 0;
}
