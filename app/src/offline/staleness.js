/*
  Which stored answers are out of date
  ====================================
  The API keeps a log of content changes (office/offline_content.py). Each
  sync asks for the changes after the last one this device saw and notes
  them here, with the time it learned of them. A note has `dates` (ranges
  of dates that changed) and `all` (some change covers every date). An
  answer stored before a note is stale:
    'hard'  its date is in `dates`, or `all` is urgent: download again at
            the next sync
    'soft'  `all` from admin edits: download again once its day is today or
            tomorrow, or whenever it is opened online
  Stored answers are never rewritten to mark them; staleness is worked out
  when they are read. The service worker adds notes of its own, and the
  apps' background downloads keep their own copy of this list and hand back
  what they learned (native.js); writes here merge with what is stored, so
  none are lost.
*/
import * as db from './db';

const MAX_KEPT = 50;
let invalidations = [];
let loaded = null;

export function loadInvalidations() {
  if (!loaded) {
    loaded = db
      .get('meta', 'invalidations')
      .then((stored) => {
        invalidations = Array.isArray(stored) ? stored : [];
      })
      .catch(() => {
        invalidations = [];
      });
  }
  return loaded;
}

// Read the list again (each sync run does: the service worker may have
// added to it since).
export function reloadInvalidations() {
  loaded = null;
  return loadInvalidations();
}

function signature(invalidation) {
  return JSON.stringify([
    invalidation.at,
    invalidation.all,
    invalidation.urgent,
    invalidation.dates,
  ]);
}

function normalize(item) {
  return {
    at: item.at,
    all: Boolean(item.all),
    urgent: Boolean(item.urgent),
    dates: Array.isArray(item.dates) ? item.dates : [],
  };
}

/*
  Save the list after `change`, merged with what is stored now: another
  writer (the service worker) may have added notes this page hasn't read.
*/
async function save(change) {
  let stored = [];
  try {
    const value = await db.get('meta', 'invalidations');
    if (Array.isArray(value)) stored = value;
  } catch {
    // Write what this page knows.
  }
  const known = new Set(invalidations.map(signature));
  const merged = [
    ...invalidations,
    ...stored.filter((item) => !known.has(signature(item))),
  ].sort((a, b) => a.at - b.at);
  invalidations = fold(change(merged));
  await db.meta.set('invalidations', invalidations);
}

/*
  Keep the list to MAX_KEPT by folding the oldest notes into one, rather
  than dropping them: an answer older than all of them would otherwise lose
  its mark. The folded note is as late as the latest of them and covers all
  they covered, so it marks at least what they did.
*/
function fold(list) {
  if (list.length <= MAX_KEPT) return list;
  const folded = list.slice(0, list.length - MAX_KEPT + 1);
  const note = {
    at: Math.max(...folded.map((item) => item.at)),
    all: folded.some((item) => item.all),
    urgent: folded.some((item) => item.all && item.urgent),
    dates: mergeDates(folded.flatMap((item) => item.dates || [])),
  };
  return [note, ...list.slice(list.length - MAX_KEPT + 1)];
}

// ISO [first, last] ranges, overlapping ones merged.
function mergeDates(ranges) {
  const merged = [];
  [...ranges]
    .sort((a, b) => (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0))
    .forEach(([first, last]) => {
      const previous = merged[merged.length - 1];
      if (previous && first <= previous[1]) {
        if (last > previous[1]) previous[1] = last;
      } else {
        merged.push([first, last]);
      }
    });
  return merged;
}

function monthEnd(isoFirst) {
  const [year, month] = isoFirst.split('-').map(Number);
  const last = new Date(year, month, 0).getDate();
  return `${isoFirst.slice(0, 8)}${String(last).padStart(2, '0')}`;
}

function datesCover(invalidation, record) {
  if (!record.date) return false;
  const start = record.date;
  const end = record.kind === 'month' ? monthEnd(record.date) : record.date;
  return (invalidation.dates || []).some(
    ([first, last]) => first <= end && last >= start
  );
}

export function stalenessOf(record) {
  let result = null;
  for (const invalidation of invalidations) {
    if (invalidation.at <= record.fetchedAt) continue;
    if (datesCover(invalidation, record)) return 'hard';
    if (!invalidation.all) continue;
    if (invalidation.urgent) return 'hard';
    result = 'soft';
  }
  return result;
}

export async function addInvalidation(summary, at = Date.now()) {
  await loadInvalidations();
  const note = normalize({ ...summary, at });
  if (!note.all && !note.dates.length) return;
  await save((list) => [...list, note]);
}

// The changes known now (for the apps' background downloads, native.js).
export async function currentInvalidations() {
  await loadInvalidations();
  return invalidations.slice();
}

/*
  Add changes learned elsewhere (the apps' background downloads, native.js),
  skipping ones already noted. Returns how many were new.
*/
export async function mergeInvalidations(list) {
  await loadInvalidations();
  const known = new Set(invalidations.map(signature));
  const added = (Array.isArray(list) ? list : [])
    .filter((item) => item && typeof item.at === 'number')
    .map(normalize)
    .filter((item) => item.all || item.dates.length)
    .filter((item) => !known.has(signature(item)));
  if (!added.length) return 0;
  await save((merged) => {
    const seen = new Set(merged.map(signature));
    return [
      ...merged,
      ...added.filter((item) => !seen.has(signature(item))),
    ].sort((a, b) => a.at - b.at);
  });
  return added.length;
}

// Forget changes older than every stored answer.
export async function trimInvalidations(oldestFetchedAt) {
  await loadInvalidations();
  if (invalidations.every((i) => i.at > oldestFetchedAt)) return;
  await save((list) => list.filter((i) => i.at > oldestFetchedAt));
}

// Tests only.
export function resetInvalidationsForTests(list = []) {
  invalidations = list;
  loaded = Promise.resolve();
}
