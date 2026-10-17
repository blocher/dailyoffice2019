import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('@/router', () => ({
  default: { currentRoute: { _value: { query: {} } }, replace: vi.fn() },
}));
vi.mock('@/helpers/storage', () => ({
  DynamicStorage: {
    getItem: vi.fn(async () => ''),
    setItem: vi.fn(async () => ''),
  },
}));
vi.mock('@/ui/feedback', () => ({ toast: { warning: vi.fn() } }));

async function load() {
  vi.resetModules();
  return (await import('@/store')).default;
}

describe('initializeSettings', () => {
  beforeEach(() => vi.clearAllMocks());

  it.each([{ detail: 'Server error' }, 'oops', null])(
    'tolerates available settings that are not a list (%j)',
    async (bad) => {
      const store = await load();
      store.commit('saveAvailableSettings', bad);
      await expect(store.dispatch('initializeSettings')).resolves.not.toThrow();
    }
  );
});
