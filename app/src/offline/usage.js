/*
  What this device prays: the sync engine downloads Family Prayer and the
  Readings page only when they have been opened lately.
*/
import * as db from './db';

const RECENT_MS = 45 * 24 * 3600 * 1000;
const usage = {};
let loaded = null;

export function loadUsage() {
  if (!loaded) {
    loaded = db
      .get('meta', 'usage')
      .then((stored) => Object.assign(usage, stored || {}))
      .catch(() => usage);
  }
  return loaded;
}

export function noteUse(kind) {
  const now = Date.now();
  // Once an hour is plenty.
  if (usage[kind] && now - usage[kind] < 3600 * 1000) return;
  usage[kind] = now;
  db.meta.set('usage', { ...usage }).catch(() => {});
}

export async function usedRecently(kind) {
  await loadUsage();
  return Boolean(usage[kind]) && Date.now() - usage[kind] < RECENT_MS;
}
