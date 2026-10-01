import { describe, it, expect, vi } from 'vitest';

const store = {};

vi.mock('./storage', () => ({
  DynamicStorage: {
    getItem: vi.fn(async (key) => (key in store ? store[key] : null)),
    setItem: vi.fn(async (key, value) => {
      store[key] = value;
      return value;
    }),
    deleteItem: vi.fn(async (key) => {
      delete store[key];
    }),
  },
}));

import { getClientId, getCachedClientId } from './clientId';
import { DynamicStorage } from './storage';

describe('clientId helper', () => {
  it('generates an id once and reuses it', async () => {
    const first = await getClientId();
    expect(first).toBeTruthy();
    expect(DynamicStorage.setItem).toHaveBeenCalledTimes(1);

    const second = await getClientId();
    expect(second).toBe(first);
    // No second write: the id is cached and persisted only once.
    expect(DynamicStorage.setItem).toHaveBeenCalledTimes(1);
  });

  it('exposes the cached id synchronously after resolution', async () => {
    const id = await getClientId();
    expect(getCachedClientId()).toBe(id);
  });
});
