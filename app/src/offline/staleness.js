/*
  Which stored answers are out of date
  ====================================
  The API keeps a log of content changes (office/offline_content.py). Each
  sync asks for the changes after the last one this device saw and notes
  them here, with the time it learned of them. An answer stored before a
  change that covers its date is stale:
    'hard'  dated or urgent changes: download again at the next sync
    'soft'  every-date changes from admin edits: download again once its day
            is today or tomorrow, or whenever it is opened online
  Stored answers are never rewritten to mark them; staleness is worked out
  when they are read.
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

function monthEnd(isoFirst) {
  const [year, month] = isoFirst.split('-').map(Number);
  const last = new Date(year, month, 0).getDate();
  return `${isoFirst.slice(0, 8)}${String(last).padStart(2, '0')}`;
}

function covers(invalidation, record) {
  if (invalidation.all) return true;
  if (!record.date) return false;
  const start = record.date;
  const end = record.kind === 'month' ? monthEnd(record.date) : record.date;
  return invalidation.dates.some(
    ([first, last]) => first <= end && last >= start
  );
}

export function stalenessOf(record) {
  let result = null;
  for (const invalidation of invalidations) {
    if (invalidation.at <= record.fetchedAt) continue;
    if (!covers(invalidation, record)) continue;
    if (invalidation.urgent || !invalidation.all) return 'hard';
    result = 'soft';
  }
  return result;
}

export async function addInvalidation(summary, at = Date.now()) {
  await loadInvalidations();
  if (!summary.all && !(summary.dates || []).length) return;
  invalidations = [
    ...invalidations,
    {
      at,
      all: Boolean(summary.all),
      urgent: Boolean(summary.urgent),
      dates: summary.all ? [] : summary.dates,
    },
  ].slice(-MAX_KEPT);
  await db.meta.set('invalidations', invalidations);
}

// Forget changes older than every stored answer.
export async function trimInvalidations(oldestFetchedAt) {
  await loadInvalidations();
  const kept = invalidations.filter((i) => i.at > oldestFetchedAt);
  if (kept.length !== invalidations.length) {
    invalidations = kept;
    await db.meta.set('invalidations', invalidations);
  }
}

// Tests only.
export function resetInvalidationsForTests(list = []) {
  invalidations = list;
  loaded = Promise.resolve();
}
