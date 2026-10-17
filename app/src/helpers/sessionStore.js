// When the browser blocks site data, even reading window.sessionStorage
// throws a SecurityError. Short-lived UI flags go through here instead:
// these never throw, and values are kept in memory too so the flags still
// work for the rest of the page load.
const memory = new Map();

function sessionStorage() {
  try {
    return window.sessionStorage || null;
  } catch {
    return null;
  }
}

export const SessionStore = {
  getItem(key) {
    try {
      const value = sessionStorage()?.getItem(key);
      if (value !== null && value !== undefined) return value;
    } catch {
      // Storage unavailable: fall back to memory.
    }
    return memory.has(key) ? memory.get(key) : null;
  },
  setItem(key, value) {
    memory.set(key, String(value));
    try {
      sessionStorage()?.setItem(key, String(value));
    } catch {
      // Storage unavailable: the in-memory copy stands in.
    }
  },
  removeItem(key) {
    memory.delete(key);
    try {
      sessionStorage()?.removeItem(key);
    } catch {
      // Storage unavailable: nothing persisted to remove.
    }
  },
};
