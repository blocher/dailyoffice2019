import { afterEach, describe, expect, it, vi } from 'vitest';

// A stand-in for indexedDB.open that fires onupgradeneeded the way some
// WebKit builds do: before the request holds a database.
function stubIndexedDb({ result }) {
  const transaction = { abort: vi.fn() };
  const request = { result, transaction };
  const open = vi.fn(() => {
    queueMicrotask(() => request.onupgradeneeded?.({ target: request }));
    return request;
  });
  vi.stubGlobal('indexedDB', { open });
  window.indexedDB = globalThis.indexedDB;
  return { request, transaction, open };
}

describe('opening the offline database', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    delete window.indexedDB;
    vi.resetModules();
  });

  it('falls back to memory when the upgrade has no database', async () => {
    const { transaction } = stubIndexedDb({ result: undefined });
    const db = await import('@/offline/db');

    await expect(db.openDb()).resolves.toBeNull();
    expect(transaction.abort).toHaveBeenCalled();

    // Still works, from memory.
    await db.put('meta', 42, 'answer');
    await expect(db.get('meta', 'answer')).resolves.toBe(42);
  });

  it('creates the stores on a real upgrade', async () => {
    const created = [];
    const database = {
      objectStoreNames: { contains: () => false },
      createObjectStore: vi.fn((name) => {
        created.push(name);
        return { createIndex: vi.fn() };
      }),
    };
    const { request } = stubIndexedDb({ result: database });
    const db = await import('@/offline/db');
    const opened = db.openDb();
    await Promise.resolve();
    await Promise.resolve();
    request.onsuccess();

    await expect(opened).resolves.toBe(database);
    expect(created).toEqual(['responses', 'audio', 'meta', 'views']);
  });
});
