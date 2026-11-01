/*
  Background downloads in the iOS and Android apps
  ================================================
  The apps can't run this code in the background, and their background
  tasks can't reach the web view's IndexedDB. So the local OfflineSync
  plugin does the work natively:
    - iOS:     ios/App/App/OfflineSyncPlugin.swift (a BGAppRefreshTask,
               every six hours or so, when iOS allows)
    - Android: android/.../offline/ (a WorkManager job every twelve hours,
               on a connection, with the battery not low)

  After each sync run, scheduleBackground() hands the plugin the download
  plan (sync.js), the content change log (staleness.js), when each planned
  answer was stored, and the audio wanted. The background task does what
  the service worker does on the web (serviceWorker.js backgroundRefresh):
  it asks what content changed, then downloads up to 80 missing or stale
  answers for today onward, each into a file in an inbox, and the audio
  tracks for today and tomorrow when offline audio is on.

  When the app opens or comes back to the front, drainInbox() moves the
  inbox into storage, keeping each answer's download time, merges the
  changes the task learned, and lets the plugin delete what was moved.

  Everywhere else (browsers) these do nothing.
*/
import { reactive } from 'vue';
import { Capacitor, registerPlugin } from '@capacitor/core';
import * as db from './db';
import {
  keepable,
  readEntry,
  readStoredInfo,
  storeEntry,
} from './cacheAdapter';
import { describe, parseApiUrl, keyFor } from './keys';
import { currentInvalidations, mergeInvalidations } from './staleness';
import { trackKey } from './audio';
import { resolveAudioUrl } from '@/helpers/officeAudio';

const OfflineSync = registerPlugin('OfflineSync');

const DRAIN_BATCH = 20;
// A full inbox is 80 answers a run; this stops a runaway loop.
const MAX_DRAIN_ROUNDS = 50;

export const nativeSyncState = reactive({
  // The plugin accepted the plan and the system will run it in the background.
  scheduled: false,
  lastDrainedAt: null,
  drained: 0,
});

export function nativeSyncAvailable() {
  return (
    Capacitor.isNativePlatform() && Capacitor.isPluginAvailable('OfflineSync')
  );
}

// The track a stored office-with-audio answer points to, when it is stored.
async function storedTrack(key) {
  const record = await readEntry(key);
  const raw = record?.data?.audio?.single_track?.[0];
  if (!raw) return null;
  const url = trackKey(resolveAudioUrl(raw));
  try {
    return (await db.get('audio', url)) ? url : null;
  } catch {
    return null;
  }
}

async function audioTasks(items) {
  const tasks = [];
  for (const item of items || []) {
    const parsed = parseApiUrl(item.url);
    const info = parsed && describe(parsed.path, parsed.query);
    if (!info) continue;
    const key = keyFor(parsed.path, parsed.query);
    tasks.push({
      url: item.url,
      key,
      kind: info.kind,
      date: item.date,
      office: item.office,
      profile: info.profile,
      // Already downloaded: the task leaves it alone.
      track: await storedTrack(key),
    });
  }
  return tasks;
}

/*
  Hand the background task its plan (null or no tasks: stop, and forget
  what it downloaded and hasn't handed over). `audio` lists the offices
  whose audio is wanted, as { url, date, office }.
*/
export async function scheduleBackground(plan, { audio = [] } = {}) {
  if (!nativeSyncAvailable()) return false;
  try {
    const tasks = plan?.tasks || [];
    const fetched = {};
    const records = await Promise.all(
      tasks.map((task) => readStoredInfo(task.key))
    );
    records.forEach((record, index) => {
      if (record) fetched[tasks[index].key] = record.fetchedAt;
    });
    const audioList = tasks.length ? await audioTasks(audio) : [];
    const result = await OfflineSync.schedule({
      plan: plan && tasks.length ? plan : { tasks: [] },
      contentVersion: (await db.meta.get('contentVersion')) || 0,
      invalidations: await currentInvalidations(),
      fetched,
      audio: { enabled: audioList.length > 0, tasks: audioList },
    });
    nativeSyncState.scheduled = Boolean(result?.scheduled);
    return nativeSyncState.scheduled;
  } catch (error) {
    nativeSyncState.scheduled = false;
    // eslint-disable-next-line no-console
    console.warn('Background downloads could not be scheduled', error);
    return false;
  }
}

// Keep one inbox entry. 'stored', 'skipped' (nothing to keep, or storage
// already has a newer copy) or 'failed' (storage full: leave it there).
async function keepEntry(entry) {
  if (!entry?.key || typeof entry.body !== 'string') return 'skipped';
  let data;
  try {
    data = JSON.parse(entry.body);
  } catch {
    return 'skipped';
  }
  if (!keepable(entry.kind, data)) return 'skipped';
  const existing = await readStoredInfo(entry.key);
  if (existing && existing.fetchedAt >= entry.fetchedAt) return 'skipped';
  const record = await storeEntry(
    entry.key,
    {
      kind: entry.kind,
      date: entry.date ?? null,
      profile: entry.profile ?? null,
    },
    entry.url,
    data,
    { fetchedAt: entry.fetchedAt }
  );
  return record ? 'stored' : 'failed';
}

// What the task learned besides answers: the content version, the
// changes, and audio tracks it saved.
async function mergeLearned(result) {
  if (typeof result.contentVersion === 'number') {
    const known = (await db.meta.get('contentVersion')) || 0;
    if (result.contentVersion > known) {
      await db.meta.set('contentVersion', result.contentVersion);
    }
  }
  const invalidations = Array.isArray(result.invalidations)
    ? result.invalidations
    : [];
  await mergeInvalidations(invalidations);
  const tracks = Array.isArray(result.audio) ? result.audio : [];
  for (const track of tracks) {
    if (!track?.url || !track.path) continue;
    if (await db.get('audio', track.url)) continue;
    await db.put('audio', {
      url: track.url,
      path: track.path,
      bytes: Number(track.bytes) || 0,
      date: track.date,
      office: track.office,
      savedAt: track.savedAt || Date.now(),
    });
  }
  return {
    invalidationsThrough: invalidations.reduce(
      (latest, item) => Math.max(latest, Number(item?.at) || 0),
      0
    ),
    audio: tracks.map((track) => track?.url).filter(Boolean),
  };
}

async function drain() {
  let stored = 0;
  for (let round = 0; round < MAX_DRAIN_ROUNDS; round += 1) {
    const result = (await OfflineSync.drain({ limit: DRAIN_BATCH })) || {};
    const learned = await mergeLearned(result);
    const keys = [];
    let full = false;
    for (const entry of result.entries || []) {
      const outcome = await keepEntry(entry);
      if (outcome === 'failed') {
        full = true;
        break;
      }
      if (outcome === 'stored') stored += 1;
      keys.push(entry.key);
    }
    await OfflineSync.ack({ keys, ...learned });
    if (full || !keys.length || !result.remaining) break;
  }
  return stored;
}

let draining = null;

/*
  Move what the background task downloaded into storage. Resolves to the
  number of answers stored; never rejects.
*/
export function drainInbox() {
  if (!nativeSyncAvailable()) return Promise.resolve(0);
  if (!draining) {
    draining = drain()
      .then((stored) => {
        nativeSyncState.lastDrainedAt = Date.now();
        nativeSyncState.drained = stored;
        return stored;
      })
      .catch((error) => {
        // eslint-disable-next-line no-console
        console.warn('Background downloads could not be moved in', error);
        return 0;
      })
      .finally(() => {
        draining = null;
      });
  }
  return draining;
}
