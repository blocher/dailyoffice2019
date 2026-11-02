import { beforeEach, describe, expect, it, vi } from 'vitest';

const stored = vi.hoisted(() => new Map());
vi.mock('@capacitor/preferences', () => ({
  Preferences: {
    get: async ({ key }) => ({ value: stored.get(key) ?? null }),
    set: async ({ key, value }) => stored.set(key, value),
    remove: async ({ key }) => stored.delete(key),
  },
}));

import { loadOfflinePrefs, offlinePrefs } from '@/offline/preferences';
import { buildPlan } from '@/offline/sync';

const SETTINGS = { psalter: '60', language_style: 'contemporary' };
const READINGS = {
  translation: 'esv',
  psalms: 'contemporary',
  style: 'whole_verse',
};

beforeEach(() => stored.clear());

describe('offline defaults', () => {
  it('keeps Family Prayer and the readings unless they were turned off', async () => {
    await loadOfflinePrefs();
    expect(offlinePrefs.family).toBe('on');
    expect(offlinePrefs.readings).toBe('on');
  });

  it("treats the old 'auto' Family Prayer choice as on", async () => {
    stored.set('offline_family', 'auto');
    await loadOfflinePrefs();
    expect(offlinePrefs.family).toBe('on');
  });

  it('keeps a choice to turn either off', async () => {
    stored.set('offline_family', 'off');
    stored.set('offline_readings', 'off');
    await loadOfflinePrefs();
    expect(offlinePrefs.family).toBe('off');
    expect(offlinePrefs.readings).toBe('off');
  });

  it('downloads the readings for every day kept, not just two weeks', () => {
    const plan = buildPlan({
      now: new Date(2026, 10, 1, 8, 0),
      days: 30,
      settings: SETTINGS,
      family: true,
      readings: READINGS,
    });
    expect(plan.filter((t) => t.kind === 'readings')).toHaveLength(30);
    expect(plan.filter((t) => t.serviceType === 'family')).toHaveLength(120);
  });
});
