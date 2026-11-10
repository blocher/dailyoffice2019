import { reactive } from 'vue';

/*
  The reader's own prayer list, offered at the intercessions. Kept only in
  this browser's localStorage. Storage can be blocked outright (reading
  window.localStorage then throws), so every access is guarded and the list
  falls back to lasting for this page view.
*/
export const PRAYER_REQUESTS_KEY = 'prayerRequests';

function getStorage() {
  try {
    return typeof window === 'undefined' ? null : window.localStorage || null;
  } catch {
    return null;
  }
}

function read() {
  const storage = getStorage();
  if (!storage) return [];
  try {
    const parsed = JSON.parse(storage.getItem(PRAYER_REQUESTS_KEY) || '[]');
    return Array.isArray(parsed)
      ? parsed.filter((item) => item && typeof item.id === 'string')
      : [];
  } catch {
    return [];
  }
}

function write(items) {
  const storage = getStorage();
  if (!storage) return;
  try {
    storage.setItem(PRAYER_REQUESTS_KEY, JSON.stringify(items));
  } catch {
    // Storage full or blocked: the change lasts for this page view.
  }
}

// Shared so the office page and the book view show the same list.
export const prayerRequests = reactive({ items: read() });

function newId() {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

export function addPrayerRequest({ name, request }) {
  const item = {
    id: newId(),
    name: String(name || '').trim(),
    request: String(request || '').trim(),
    createdAt: new Date().toISOString(),
  };
  if (!item.name && !item.request) return null;
  prayerRequests.items = [...prayerRequests.items, item];
  write(prayerRequests.items);
  return item;
}

export function updatePrayerRequest(id, { name, request }) {
  prayerRequests.items = prayerRequests.items.map((item) =>
    item.id === id
      ? {
          ...item,
          name: String(name || '').trim(),
          request: String(request || '').trim(),
        }
      : item
  );
  write(prayerRequests.items);
}

export function removePrayerRequest(id) {
  prayerRequests.items = prayerRequests.items.filter((item) => item.id !== id);
  write(prayerRequests.items);
}

// Re-read storage (another tab may have changed it); used by tests too.
export function reloadPrayerRequests() {
  prayerRequests.items = read();
}
