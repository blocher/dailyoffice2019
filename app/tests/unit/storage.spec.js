import { beforeEach, describe, expect, it, vi } from 'vitest';

const preferences = vi.hoisted(() => ({
  set: vi.fn(),
  get: vi.fn(),
  remove: vi.fn(),
}));
vi.mock('@capacitor/preferences', () => ({ Preferences: preferences }));

async function load() {
  vi.resetModules();
  return (await import('@/helpers/storage')).DynamicStorage;
}

function denied() {
  return Promise.reject(
    new DOMException('Access is denied for this document.', 'SecurityError')
  );
}

describe('DynamicStorage when storage is blocked', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    preferences.set.mockImplementation(denied);
    preferences.get.mockImplementation(denied);
    preferences.remove.mockImplementation(denied);
  });

  it('does not throw on set and serves the value back from memory', async () => {
    const storage = await load();
    await expect(storage.setItem('settings', '{"a":1}')).resolves.toBe(
      '{"a":1}'
    );
    await expect(storage.getItem('settings')).resolves.toBe('{"a":1}');
  });

  it('returns an empty string for unknown keys and tolerates delete', async () => {
    const storage = await load();
    await expect(storage.getItem('missing')).resolves.toBe('');
    await expect(storage.deleteItem('missing')).resolves.toBeUndefined();
  });

  it('still reads persisted values when storage works', async () => {
    preferences.get.mockResolvedValue({ value: 'saved' });
    const storage = await load();
    await expect(storage.getItem('k')).resolves.toBe('saved');
  });
});
