/*
  Lists of ids kept in localStorage or sessionStorage (dismissed messages,
  seen What's New entries). Browsers can deny storage outright, and reading
  window.localStorage itself then throws a SecurityError, so every access is
  guarded: a blocked list reads as empty and writes last only for the page.
*/
function getStorage(name) {
  try {
    return typeof window === 'undefined' ? null : window[name] || null;
  } catch {
    return null;
  }
}

export function readStoredList(storageName, key) {
  const storage = getStorage(storageName);
  if (!storage) return [];
  try {
    const parsed = JSON.parse(storage.getItem(key) || '[]');
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function addToStoredList(storageName, key, ids) {
  const storage = getStorage(storageName);
  if (!storage) return;
  const stored = readStoredList(storageName, key);
  const added = ids.filter((id) => !stored.includes(id));
  if (!added.length) return;
  try {
    storage.setItem(key, JSON.stringify([...stored, ...added]));
  } catch {
    // Storage full or blocked: the change lasts for this page view.
  }
}
