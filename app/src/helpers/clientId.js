import { DynamicStorage } from './storage';

// A stable, first-party anonymous identifier used to distinguish unique users
// in our own analytics and to reconcile with Google Analytics. It is generated
// once and persisted in Capacitor Preferences (survives reloads and, on native,
// app restarts). It contains no personal information.
const CLIENT_ID_KEY = 'anonymous_client_id';

let cachedClientId = null;

function generateId() {
  if (window.crypto && typeof window.crypto.randomUUID === 'function') {
    return window.crypto.randomUUID();
  }
  // Fallback for older webviews without crypto.randomUUID.
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export async function getClientId() {
  if (cachedClientId) {
    return cachedClientId;
  }
  let id = await DynamicStorage.getItem(CLIENT_ID_KEY);
  if (!id) {
    id = generateId();
    await DynamicStorage.setItem(CLIENT_ID_KEY, id);
  }
  cachedClientId = id;
  return id;
}

// Synchronous accessor for code paths that can't await (e.g. building a URL).
// Returns null until getClientId() has resolved at least once during bootstrap.
export function getCachedClientId() {
  return cachedClientId;
}
