/*
  Office audio kept for offline listening
  =======================================
  Opt-in (Offline settings): the sync engine downloads the combined audio
  track for chosen offices today and tomorrow. A track can be 30 MB, so it
  is never downloaded without being asked for.

  - Web and installed web app: the MP3 is kept in IndexedDB and played from
    a blob: URL.
  - iOS and Android apps: the MP3 is downloaded natively to a file outside
    the iCloud backup (Library/NoCloud on iOS, app files on Android) and the
    native player (helpers/nativeAudio.js) plays the file.

  A stored track plays even online: it starts at once and saves the data.
*/
import { Capacitor } from '@capacitor/core';
import * as db from './db';
import { hashString } from './keys';
import { SYNC_HEADER } from './cacheAdapter';
import { nativeAudioAvailable } from '@/helpers/nativeAudio';

const NATIVE_DIR = 'offline-audio';
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

export async function hasTrack(url) {
  try {
    return Boolean(await db.get('audio', trackKey(url)));
  } catch {
    return false;
  }
}

async function saveWeb(url, info) {
  const response = await window.fetch(url, { headers: { [SYNC_HEADER]: '1' } });
  if (!response.ok)
    throw new Error(`Audio download failed (${response.status})`);
  const expected = Number(response.headers.get('content-length')) || 0;
  const blob = await response.blob();
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
  const { uri } = await Filesystem.getUri({
    path,
    directory: Directory.LibraryNoCloud,
  });
  await FileTransfer.downloadFile({
    url,
    path: uri,
    headers: { [SYNC_HEADER]: '1' },
  });
  const stat = await Filesystem.stat({
    path,
    directory: Directory.LibraryNoCloud,
  });
  if (!stat.size) throw new Error('Audio download was empty');
  await db.put('audio', {
    url,
    path,
    uri,
    bytes: Number(stat.size) || 0,
    date: info.date,
    office: info.office,
    savedAt: Date.now(),
  });
  return Number(stat.size) || 0;
}

// Download one track; resolves to its size in bytes.
export async function saveTrack(rawUrl, info = {}) {
  const url = trackKey(rawUrl);
  const existing = await db.get('audio', url);
  if (existing) return existing.bytes || 0;
  return isNative() ? saveNative(url, info) : saveWeb(url, info);
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
    record = await db.get('audio', url);
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
  if (record.uri) {
    return nativeAudioAvailable()
      ? record.uri
      : Capacitor.convertFileSrc(record.uri);
  }
  return null;
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
