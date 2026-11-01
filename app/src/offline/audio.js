/*
  Office audio kept for offline listening
  =======================================
  Opt-in (Offline settings): the sync engine downloads the combined audio
  track for chosen offices today and tomorrow. A track can be 30 MB, so it
  is never downloaded without being asked for.

  - Web and installed web app: the MP3 is kept in IndexedDB and played from
    a blob: URL.
  - iOS and Android apps: the MP3 is downloaded natively to a file kept out
    of backups (Library/NoCloud on iOS; on Android, app files excluded by
    res/xml/backup_rules.xml) and the native player (helpers/nativeAudio.js)
    plays the file.

  A stored track plays even online: it starts at once and saves the data.
*/
import { Capacitor } from '@capacitor/core';
import * as db from './db';
import { hashString } from './keys';
import { SYNC_HEADER } from './cacheAdapter';
import { nativeAudioAvailable } from '@/helpers/nativeAudio';

const NATIVE_DIR = 'offline-audio';
// A web download that receives nothing for this long has stalled (a captive
// portal, a half-open connection): give up, and try again next run.
const STALLED_MS = 60 * 1000;
const objectUrls = new Map();

function isNative() {
  return Capacitor.isNativePlatform();
}

async function nativeModules() {
  const [{ Filesystem, Directory }, { FileTransfer }] = await Promise.all([
    import('@capacitor/filesystem'),
    import('@capacitor/file-transfer'),
  ]);
  return { Filesystem, Directory, FileTransfer };
}

// The address a track is stored under: without the "reload" retry token.
export function trackKey(url) {
  try {
    const parsed = new window.URL(url, window.location.href);
    parsed.searchParams.delete('reload');
    return parsed.toString();
  } catch {
    return url;
  }
}

/*
  The stored record for a track, or null. In the apps, a record whose file
  is gone (the files aren't backed up, but the web view's storage is, so a
  restored phone has records without files) is removed, and the track
  counts as not stored.
*/
async function storedRecord(url) {
  const record = await db.get('audio', url);
  if (!record?.path || !isNative()) return record || null;
  try {
    const { Filesystem, Directory } = await nativeModules();
    await Filesystem.stat({
      path: record.path,
      directory: Directory.LibraryNoCloud,
    });
    return record;
  } catch {
    await db.remove('audio', url).catch(() => {});
    return null;
  }
}

export async function hasTrack(url) {
  try {
    return Boolean(await storedRecord(trackKey(url)));
  } catch {
    return false;
  }
}

// The body of a download, given up on when it stalls or `signal` aborts.
async function readBody(url, signal) {
  const controller = new window.AbortController();
  const stop = () => controller.abort();
  if (signal?.aborted) stop();
  signal?.addEventListener('abort', stop, { once: true });
  let timer = null;
  const stillGoing = () => {
    window.clearTimeout(timer);
    timer = window.setTimeout(stop, STALLED_MS);
  };
  try {
    stillGoing();
    const response = await window.fetch(url, {
      headers: { [SYNC_HEADER]: '1' },
      signal: controller.signal,
    });
    if (!response.ok)
      throw new Error(`Audio download failed (${response.status})`);
    const expected = Number(response.headers.get('content-length')) || 0;
    const type = response.headers.get('content-type') || 'audio/mpeg';
    if (!response.body?.getReader)
      return { blob: await response.blob(), expected };
    const reader = response.body.getReader();
    const chunks = [];
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      chunks.push(value);
      stillGoing();
    }
    return { blob: new window.Blob(chunks, { type }), expected };
  } finally {
    window.clearTimeout(timer);
    signal?.removeEventListener('abort', stop);
  }
}

async function saveWeb(url, info, { signal } = {}) {
  const { blob, expected } = await readBody(url, signal);
  if (expected && blob.size < expected) {
    throw new Error('Audio download was cut off');
  }
  await db.put('audio', {
    url,
    blob,
    bytes: blob.size,
    date: info.date,
    office: info.office,
    savedAt: Date.now(),
  });
  return blob.size;
}

async function saveNative(url, info) {
  const { Filesystem, Directory, FileTransfer } = await nativeModules();
  const path = `${NATIVE_DIR}/${hashString(url)}.mp3`;
  try {
    await Filesystem.mkdir({
      path: NATIVE_DIR,
      directory: Directory.LibraryNoCloud,
      recursive: true,
    });
  } catch {
    // Already there.
  }
  // Downloaded beside the track and moved into place once whole: a file at
  // `path` is always a finished track (the Android background run trusts
  // that too). Android's transfer writes straight into its target and
  // leaves what it got when cut off.
  const partial = `${path}.part`;
  const { uri } = await Filesystem.getUri({
    path: partial,
    directory: Directory.LibraryNoCloud,
  });
  let stat;
  try {
    await FileTransfer.downloadFile({
      url,
      path: uri,
      headers: { [SYNC_HEADER]: '1' },
    });
    stat = await Filesystem.stat({
      path: partial,
      directory: Directory.LibraryNoCloud,
    });
    if (!stat.size) throw new Error('Audio download was empty');
    // The background run may have put the same track there meanwhile.
    await Filesystem.deleteFile({
      path,
      directory: Directory.LibraryNoCloud,
    }).catch(() => {});
    await Filesystem.rename({
      from: partial,
      to: path,
      directory: Directory.LibraryNoCloud,
      toDirectory: Directory.LibraryNoCloud,
    });
  } catch (error) {
    await Filesystem.deleteFile({
      path: partial,
      directory: Directory.LibraryNoCloud,
    }).catch(() => {});
    throw error;
  }
  // Only the path: the app's folder can move when the app is updated.
  await db.put('audio', {
    url,
    path,
    bytes: Number(stat.size) || 0,
    date: info.date,
    office: info.office,
    savedAt: Date.now(),
  });
  return Number(stat.size) || 0;
}

// Download one track; resolves to its size in bytes. `signal` stops a web
// download (the apps' transfers run to the end).
export async function saveTrack(rawUrl, info = {}, { signal } = {}) {
  const url = trackKey(rawUrl);
  const existing = await storedRecord(url);
  if (existing) return existing.bytes || 0;
  return isNative() ? saveNative(url, info) : saveWeb(url, info, { signal });
}

/*
  A playable address for a stored track, or null. Native players take the
  file itself; a web view's <audio> takes it through Capacitor's file
  server; browsers take a blob: URL.
*/
export async function localTrackUrl(rawUrl) {
  const url = trackKey(rawUrl);
  let record;
  try {
    record = await storedRecord(url);
  } catch {
    return null;
  }
  if (!record) return null;
  if (record.blob) {
    if (!objectUrls.has(url)) {
      objectUrls.set(url, window.URL.createObjectURL(record.blob));
    }
    return objectUrls.get(url);
  }
  const uri = await nativeFileUri(record);
  if (uri) {
    return nativeAudioAvailable() ? uri : Capacitor.convertFileSrc(uri);
  }
  return null;
}

// Where a natively stored track is now. iOS moves the app's folder when the
// app is updated, so the address is worked out from the path each time
// (older downloads also kept the address they were saved at).
async function nativeFileUri(record) {
  if (record.path && isNative()) {
    try {
      const { Filesystem, Directory } = await nativeModules();
      const { uri } = await Filesystem.getUri({
        path: record.path,
        directory: Directory.LibraryNoCloud,
      });
      if (uri) return uri;
    } catch {
      // Fall back to the saved address.
    }
  }
  return record.uri || null;
}

async function deleteRecord(record) {
  if (objectUrls.has(record.url)) {
    window.URL.revokeObjectURL(objectUrls.get(record.url));
    objectUrls.delete(record.url);
  }
  if (record.path && isNative()) {
    try {
      const { Filesystem, Directory } = await nativeModules();
      await Filesystem.deleteFile({
        path: record.path,
        directory: Directory.LibraryNoCloud,
      });
    } catch {
      // Already gone.
    }
  }
  await db.remove('audio', record.url);
}

// Remove every stored track not in `keep` (a Set of track URLs).
export async function pruneTracks(keep) {
  const all = await db.getAll('audio');
  await Promise.all(
    all.filter((record) => !keep.has(record.url)).map(deleteRecord)
  );
}

// Remove stored tracks for days before `isoDate`.
export async function removeTracksBefore(isoDate) {
  const all = await db.getAll('audio');
  await Promise.all(
    all
      .filter((record) => record.date && record.date < isoDate)
      .map(deleteRecord)
  );
}

export async function clearTracks() {
  await pruneTracks(new Set());
}

export async function audioSummary() {
  const all = await db.getAll('audio');
  return {
    count: all.length,
    bytes: all.reduce((sum, record) => sum + (record.bytes || 0), 0),
    tracks: all.map(({ url, date, office, bytes }) => ({
      url,
      date,
      office,
      bytes,
    })),
  };
}
