/*
  Offline storage
  ===============
  One IndexedDB database holds everything the app keeps for offline use:
    responses  API answers, keyed by request (see keys.js)
    audio      downloaded office audio (web: the MP3 itself; apps: a file path)
    meta       small values: the content version, sync times, the plan the
               service worker follows in the background
    views      office views prayed offline, waiting to be reported

  The service worker (public/sw.js) opens the same database, so keep the
  name, version, and store layout in step with it.

  When IndexedDB isn't available (some private windows, blocked site data)
  everything falls back to memory: the app still works online, it just
  forgets on reload.
*/

export const DB_NAME = 'dailyoffice-offline';
export const DB_VERSION = 1;

const memory = {
  responses: new Map(),
  audio: new Map(),
  meta: new Map(),
  views: new Map(),
};
let memoryViewId = 1;

let opening = null;
let unavailable = false;

function promisify(request) {
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export function upgrade(db) {
  if (!db.objectStoreNames.contains('responses')) {
    const responses = db.createObjectStore('responses', { keyPath: 'key' });
    responses.createIndex('date', 'date');
    responses.createIndex('profile', 'profile');
  }
  if (!db.objectStoreNames.contains('audio')) {
    db.createObjectStore('audio', { keyPath: 'url' });
  }
  if (!db.objectStoreNames.contains('meta')) {
    db.createObjectStore('meta');
  }
  if (!db.objectStoreNames.contains('views')) {
    db.createObjectStore('views', { keyPath: 'id', autoIncrement: true });
  }
}

export function openDb() {
  if (unavailable) return Promise.resolve(null);
  if (opening) return opening;
  opening = new Promise((resolve) => {
    let request;
    try {
      if (typeof window.indexedDB === 'undefined')
        throw new Error('No IndexedDB');
      request = window.indexedDB.open(DB_NAME, DB_VERSION);
    } catch {
      unavailable = true;
      resolve(null);
      return;
    }
    request.onupgradeneeded = () => upgrade(request.result);
    request.onsuccess = () => {
      const db = request.result;
      // Another tab (or the service worker) upgrading: let it.
      db.onversionchange = () => {
        db.close();
        opening = null;
      };
      resolve(db);
    };
    request.onerror = () => {
      unavailable = true;
      resolve(null);
    };
    request.onblocked = () => {
      // An old tab holds the database open; keep working from memory.
      unavailable = true;
      resolve(null);
    };
  });
  return opening;
}

async function withStore(name, mode, run) {
  const db = await openDb();
  if (!db) return run(null);
  try {
    const tx = db.transaction(name, mode);
    const done = new Promise((resolve, reject) => {
      tx.oncomplete = resolve;
      tx.onabort = () => reject(tx.error);
      tx.onerror = () => reject(tx.error);
    });
    const [result] = await Promise.all([run(tx.objectStore(name)), done]);
    return result;
  } catch (error) {
    if (error?.name === 'QuotaExceededError') throw error;
    // A closed or broken database: answer from memory this time.
    return run(null);
  }
}

export function get(name, key) {
  return withStore(name, 'readonly', (store) =>
    store ? promisify(store.get(key)) : memory[name].get(key)
  );
}

export function put(name, value, key) {
  return withStore(name, 'readwrite', (store) => {
    if (!store) {
      if (name === 'views' && value.id === undefined) {
        value = { ...value, id: memoryViewId++ };
      }
      const id = key ?? value.key ?? value.url ?? value.id;
      memory[name].set(id, value);
      return id;
    }
    return promisify(
      key === undefined ? store.put(value) : store.put(value, key)
    );
  });
}

export function remove(name, key) {
  return withStore(name, 'readwrite', (store) =>
    store ? promisify(store.delete(key)) : memory[name].delete(key)
  );
}

export function getAll(name) {
  return withStore(name, 'readonly', (store) =>
    store ? promisify(store.getAll()) : [...memory[name].values()]
  );
}

export function getAllByIndex(name, index, value) {
  return withStore(name, 'readonly', (store) =>
    store
      ? promisify(store.index(index).getAll(value))
      : [...memory[name].values()].filter((item) => item[index] === value)
  );
}

export function clear(name) {
  return withStore(name, 'readwrite', (store) =>
    store ? promisify(store.clear()) : memory[name].clear()
  );
}

// Visit every record without loading them all at once; `visit` returns
// 'delete' to remove one, or an updated record to replace it.
export function eachRecord(name, visit) {
  return withStore(name, 'readwrite', (store) => {
    if (!store) {
      for (const [key, value] of [...memory[name].entries()]) {
        const result = visit(value);
        if (result === 'delete') memory[name].delete(key);
        else if (result && typeof result === 'object')
          memory[name].set(key, result);
      }
      return undefined;
    }
    return new Promise((resolve, reject) => {
      const request = store.openCursor();
      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        const cursor = request.result;
        if (!cursor) {
          resolve();
          return;
        }
        const result = visit(cursor.value);
        if (result === 'delete') cursor.delete();
        else if (result && typeof result === 'object') cursor.update(result);
        cursor.continue();
      };
    });
  });
}

export const meta = {
  get: (key) => get('meta', key),
  set: (key, value) => put('meta', value, key),
};

export function isPersistent() {
  return !unavailable;
}

// Tests only.
export function resetForTests() {
  opening = null;
  unavailable = false;
  Object.values(memory).forEach((map) => map.clear());
}
