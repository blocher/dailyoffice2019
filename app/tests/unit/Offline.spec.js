import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as db from '@/offline/db';
import {
  describe as describeRequest,
  keyFor,
  parseApiUrl,
  profileFor,
  profileForSettings,
} from '@/offline/keys';
import { officeUrl, readingsUrl } from '@/offline/urls';
import {
  applyStoredSummaries,
  handle,
  readStoredInfo,
  resetStoredIndex,
  SYNC_HEADER,
} from '@/offline/cacheAdapter';
import {
  reportUnreachable,
  setBrowserOnlineForTests,
  network,
} from '@/offline/network';
import {
  addInvalidation,
  resetInvalidationsForTests,
  stalenessOf,
} from '@/offline/staleness';
import { noteUse, usedRecently } from '@/offline/usage';
import { buildPlan, officeOrderFor } from '@/offline/sync';
import { estimateBytes, formatBytes, friendlyDate } from '@/offline/format';

const SETTINGS = {
  bible_translation: 'esv',
  psalter: '60',
  language_style: 'contemporary',
};

function ok(data, status = 200) {
  return {
    data: JSON.stringify(data),
    status,
    statusText: 'OK',
    headers: {},
    config: {},
  };
}

function networkError() {
  const error = new Error('Network Error');
  error.code = 'ERR_NETWORK';
  return error;
}

describe('request keys', () => {
  it('keys a request by path and sorted parameters', () => {
    const a = parseApiUrl('/api/v1/office/morning_prayer/2026-11-2?b=2&a=1');
    const b = parseApiUrl('/api/v1/office/morning_prayer/2026-11-2?a=1&b=2');
    expect(keyFor(a.path, a.query)).toBe(keyFor(b.path, b.query));
    expect(keyFor(a.path, a.query)).toBe(
      'office/morning_prayer/2026-11-2?a=1&b=2'
    );
  });

  it('keys padded and unpadded dates alike', () => {
    expect(keyFor('calendar/2026-11-02', {})).toBe('calendar/2026-11-2');
    expect(keyFor('calendar/2026-01', {})).toBe('calendar/2026-1');
    expect(keyFor('office/compline/2026-11-02', { a: '1' })).toBe(
      'office/compline/2026-11-2?a=1'
    );
    expect(keyFor('psalms/topics', {})).toBe('psalms/topics');
  });

  it('describes what each request is', () => {
    const office = describeRequest('office/evening_prayer/2026-11-2', SETTINGS);
    expect(office).toMatchObject({
      kind: 'office',
      date: '2026-11-02',
      policy: 'cache-first',
    });
    expect(
      describeRequest('family/close_of_day_prayer/2026-1-9', {}).date
    ).toBe('2026-01-09');
    expect(
      describeRequest('office/compline/2026-11-2', {
        include_audio_links: 'true',
      }).kind
    ).toBe('audio');
    expect(describeRequest('calendar/2026-11', {}).kind).toBe('month');
    expect(describeRequest('calendar/2026-11-2', {}).kind).toBe('day');
    expect(describeRequest('psalms', {}).kind).toBe('reference');
    expect(describeRequest('analytics/event', {})).toBeNull();
    expect(describeRequest('content_changes', {})).toBeNull();
    expect(describeRequest('audio_track/x.mp3', {})).toBeNull();
  });

  it('gives offices and readings for the same settings the same profile', () => {
    const office = parseApiUrl(
      officeUrl({
        serviceType: 'office',
        office: 'compline',
        date: new Date(2026, 10, 2),
        settings: SETTINGS,
      })
    );
    const readings = parseApiUrl(
      readingsUrl({
        date: new Date(2026, 10, 2),
        translation: 'kjv',
        psalms: 'x',
        style: 'y',
        settings: SETTINGS,
      })
    );
    expect(profileFor(office.query)).toBe(profileFor(readings.query));
    expect(profileFor(office.query)).toBe(profileForSettings(SETTINGS));
    expect(profileForSettings({ ...SETTINGS, psalter: '30' })).not.toBe(
      profileForSettings(SETTINGS)
    );
  });

  it('ignores requests to other hosts', () => {
    expect(parseApiUrl('https://example.com/api/v1/psalms')).toBeNull();
    expect(parseApiUrl('/not-the-api')).toBeNull();
  });
});

describe('the download plan', () => {
  it('starts with the office for this time of day', () => {
    expect(officeOrderFor(7)[0]).toBe('morning_prayer');
    expect(officeOrderFor(12)[0]).toBe('midday_prayer');
    expect(officeOrderFor(17)[0]).toBe('evening_prayer');
    expect(officeOrderFor(22)).toEqual([
      'compline',
      'morning_prayer',
      'midday_prayer',
      'evening_prayer',
    ]);
  });

  it('plans the settings list, then today, then the days ahead', () => {
    const now = new Date(2026, 10, 2, 18, 0);
    const plan = buildPlan({ now, days: 3, settings: SETTINGS });
    expect(plan[0].label).toBe('Settings');
    expect(plan[1]).toMatchObject({
      kind: 'office',
      office: 'evening_prayer',
      date: '2026-11-02',
    });
    const offices = plan.filter((t) => t.kind === 'office');
    expect(offices).toHaveLength(12);
    expect(new Set(offices.map((t) => t.date))).toEqual(
      new Set(['2026-11-02', '2026-11-03', '2026-11-04'])
    );
    expect(plan.filter((t) => t.kind === 'day')).toHaveLength(3);
    expect(plan.filter((t) => t.kind === 'month')).toHaveLength(1);
    expect(plan.filter((t) => t.kind === 'reference').length).toBeGreaterThan(
      3
    );
    // Tomorrow's offices come before the library.
    const lastOffice = plan.map((t) => t.kind).lastIndexOf('office');
    const firstLibrary = plan.findIndex((t) => t.label === 'The library');
    expect(lastOffice).toBeLessThan(firstLibrary);
  });

  it('adds Family Prayer and readings only when asked', () => {
    const now = new Date(2026, 10, 30, 8, 0);
    const plain = buildPlan({ now, days: 2, settings: SETTINGS });
    const full = buildPlan({
      now,
      days: 2,
      settings: SETTINGS,
      family: true,
      readings: {
        translation: 'esv',
        psalms: 'contemporary',
        style: 'whole_verse',
      },
    });
    expect(plain.some((t) => t.serviceType === 'family')).toBe(false);
    expect(full.filter((t) => t.serviceType === 'family')).toHaveLength(8);
    expect(full.filter((t) => t.kind === 'readings')).toHaveLength(2);
    // The window crosses into December: both months.
    expect(full.filter((t) => t.kind === 'month')).toHaveLength(2);
  });

  it('plans nothing when downloads are off', () => {
    expect(buildPlan({ days: 0, settings: SETTINGS })).toEqual([]);
    expect(buildPlan({ days: 7, settings: null })).toEqual([]);
  });
});

describe('staleness', () => {
  afterEach(() => resetInvalidationsForTests([]));

  it('applies dated, every-date, and urgent changes', () => {
    resetInvalidationsForTests([
      {
        at: 100,
        all: false,
        urgent: false,
        dates: [['2026-11-02', '2026-11-03']],
      },
      { at: 200, all: true, urgent: false, dates: [] },
    ]);
    expect(stalenessOf({ date: '2026-11-02', fetchedAt: 50 })).toBe('hard');
    expect(stalenessOf({ date: '2026-11-09', fetchedAt: 50 })).toBe('soft');
    expect(stalenessOf({ date: '2026-11-09', fetchedAt: 300 })).toBeNull();
    expect(stalenessOf({ date: null, fetchedAt: 150 })).toBe('soft');
    expect(
      stalenessOf({ kind: 'month', date: '2026-11-01', fetchedAt: 50 })
    ).toBe('hard');

    resetInvalidationsForTests([
      { at: 100, all: true, urgent: true, dates: [] },
    ]);
    expect(stalenessOf({ date: '2026-12-25', fetchedAt: 50 })).toBe('hard');
  });

  it('keeps dated changes hard when every date also changed', () => {
    resetInvalidationsForTests([
      {
        at: 100,
        all: true,
        urgent: false,
        dates: [['2026-11-20', '2026-11-20']],
      },
    ]);
    expect(stalenessOf({ date: '2026-11-20', fetchedAt: 50 })).toBe('hard');
    expect(stalenessOf({ date: '2026-11-21', fetchedAt: 50 })).toBe('soft');
  });
});

describe('the change list', () => {
  beforeEach(() => {
    db.resetForTests();
    resetStoredIndex();
    resetInvalidationsForTests([]);
  });

  it('keeps changes the service worker saved behind its back', async () => {
    await db.meta.set('invalidations', [
      {
        at: 50,
        all: false,
        urgent: false,
        dates: [['2026-11-02', '2026-11-02']],
      },
    ]);
    await addInvalidation({ all: true, urgent: false, dates: [] }, 100);
    expect((await db.meta.get('invalidations')).map((i) => i.at)).toEqual([
      50, 100,
    ]);
  });

  it('folds the oldest changes together rather than forget them', async () => {
    await addInvalidation(
      { all: false, urgent: false, dates: [['2026-11-02', '2026-11-03']] },
      1
    );
    for (let at = 2; at <= 60; at += 1) {
      await addInvalidation(
        { all: false, urgent: false, dates: [['2026-12-01', '2026-12-01']] },
        at
      );
    }
    const list = await db.meta.get('invalidations');
    expect(list).toHaveLength(50);
    expect(list[0]).toMatchObject({
      at: 11,
      dates: [
        ['2026-11-02', '2026-11-03'],
        ['2026-12-01', '2026-12-01'],
      ],
    });
    // An answer older than every change still knows its date changed.
    expect(stalenessOf({ date: '2026-11-03', fetchedAt: 0 })).toBe('hard');
  });
});

describe('noting what is used', () => {
  it('keeps the other kinds when the first use comes before loading', async () => {
    db.resetForTests();
    await db.meta.set('usage', { family: Date.now() - 1000 });
    await noteUse('office');
    expect(await usedRecently('family')).toBe(true);
    expect(Object.keys(await db.meta.get('usage')).sort()).toEqual([
      'family',
      'office',
    ]);
  });
});

describe('the offline-aware adapter', () => {
  const officeConfig = (extra = {}) => ({
    method: 'get',
    url: '/api/v1/office/morning_prayer/2026-11-2?bible_translation=esv&extra_collects=',
    headers: {},
    ...extra,
  });

  beforeEach(async () => {
    db.resetForTests();
    resetStoredIndex();
    resetInvalidationsForTests([]);
    setBrowserOnlineForTests(true);
  });

  afterEach(() => {
    setBrowserOnlineForTests(true);
    vi.useRealTimers();
  });

  it('stores what the network sends', async () => {
    const network = vi.fn().mockResolvedValue(ok({ modules: [1] }));
    const response = await handle(officeConfig(), network);
    expect(JSON.parse(response.data)).toEqual({ modules: [1] });
    await vi.waitFor(async () => {
      const stored = await db.get(
        'responses',
        'office/morning_prayer/2026-11-2?bible_translation=esv&extra_collects='
      );
      expect(stored.data).toEqual({ modules: [1] });
      expect(stored).toMatchObject({ kind: 'office', date: '2026-11-02' });
    });
  });

  it('answers an office from storage at once, and refreshes it behind', async () => {
    const network = vi.fn().mockResolvedValue(ok({ modules: ['first'] }));
    await handle(officeConfig(), network);
    network.mockResolvedValue(ok({ modules: ['second'] }));
    const response = await handle(officeConfig(), network);
    expect(response.data).toEqual({ modules: ['first'] });
    expect(response.offline).toBeTruthy();
    await vi.waitFor(async () => {
      const stored = await db.get(
        'responses',
        'office/morning_prayer/2026-11-2?bible_translation=esv&extra_collects='
      );
      expect(stored.data).toEqual({ modules: ['second'] });
    });
    expect(network).toHaveBeenCalledTimes(2);
  });

  it('answers offline from storage and queues the view', async () => {
    const network = vi.fn().mockResolvedValue(ok({ modules: [1] }));
    await handle(officeConfig(), network);
    setBrowserOnlineForTests(false);
    const response = await handle(officeConfig(), network);
    expect(response.data).toEqual({ modules: [1] });
    expect(network).toHaveBeenCalledTimes(1);
    await vi.waitFor(async () => {
      const views = await db.getAll('views');
      expect(views).toHaveLength(1);
      expect(views[0]).toMatchObject({
        service_type: 'office',
        office: 'morning_prayer',
        office_date: '2026-11-02',
      });
    });
  });

  it('fails clearly offline when nothing is stored', async () => {
    setBrowserOnlineForTests(false);
    await expect(handle(officeConfig(), vi.fn())).rejects.toMatchObject({
      isOffline: true,
    });
  });

  it('says offline when the connection fails and nothing is stored', async () => {
    await expect(
      handle(officeConfig(), vi.fn().mockRejectedValue(networkError()))
    ).rejects.toMatchObject({ isOffline: true });
  });

  it('keeps a one-off failure an error, not offline', async () => {
    // Well after the other tests' failures (two within 20 s would mean the
    // API can't be reached).
    vi.spyOn(Date, 'now').mockReturnValue(Date.now() + 60 * 1000);
    const timeout = Object.assign(new Error('timeout'), {
      code: 'ECONNABORTED',
    });
    const error = await handle(
      officeConfig(),
      vi.fn().mockRejectedValue(timeout)
    ).catch((e) => e);
    vi.restoreAllMocks();
    expect(error).toBe(timeout);
    expect(network.online).toBe(true);
  });

  it('still tries the network for what is not stored while requests fail', async () => {
    reportUnreachable();
    expect(network.online).toBe(false);
    const response = await handle(
      officeConfig(),
      vi.fn().mockResolvedValue(ok({ modules: [1] }))
    );
    expect(JSON.parse(response.data)).toEqual({ modules: [1] });
    expect(network.online).toBe(true);
  });

  it('dates a download from when it was asked for', async () => {
    let now = 1000;
    vi.spyOn(Date, 'now').mockImplementation(() => now);
    const slow = vi.fn().mockImplementation(async () => {
      now = 5000;
      return ok({ modules: [1] });
    });
    await handle(officeConfig({ headers: { [SYNC_HEADER]: '1' } }), slow);
    vi.restoreAllMocks();
    const stored = await db.get(
      'responses',
      'office/morning_prayer/2026-11-2?bible_translation=esv&extra_collects='
    );
    expect(stored.fetchedAt).toBe(1000);
  });

  it('learns what another tab or the service worker stored', async () => {
    const key = 'psalms';
    expect(await readStoredInfo(key)).toBeNull();
    applyStoredSummaries([
      { key, fetchedAt: 1, schema: 1, kind: 'reference', bytes: 2 },
    ]);
    expect(await readStoredInfo(key)).toMatchObject({ key, fetchedAt: 1 });
  });

  it('falls back to storage when the network fails', async () => {
    const config = { method: 'get', url: '/api/v1/psalms', headers: {} };
    const network = vi.fn().mockResolvedValue(ok([{ number: 1 }]));
    await handle(config, network);
    network.mockRejectedValue(networkError());
    const response = await handle(config, network);
    expect(response.data).toEqual([{ number: 1 }]);
    expect(network.mock.calls.length).toBe(2);
    expect(network.mock.results[1].type).toBe('return');
    expect(networkStateOnline()).toBe(false);
  });

  it('falls back to storage when the server errors', async () => {
    const config = { method: 'get', url: '/api/v1/psalms', headers: {} };
    await handle(config, vi.fn().mockResolvedValue(ok([{ number: 1 }])));
    await vi.waitFor(async () =>
      expect(await db.getAll('responses')).toHaveLength(1)
    );
    const failing = vi
      .fn()
      .mockRejectedValue(
        Object.assign(new Error('Bad Gateway'), { response: { status: 502 } })
      );
    const response = await handle(config, failing);
    expect(response.data).toEqual([{ number: 1 }]);
    expect(networkStateOnline()).toBe(true);
  });

  it('stays online when a write or an unstored request fails', async () => {
    const failing = vi.fn().mockRejectedValue(networkError());
    await expect(
      handle(
        { method: 'post', url: '/api/v1/analytics/event', headers: {} },
        failing
      )
    ).rejects.toThrow();
    await expect(
      handle(
        { method: 'get', url: '/api/v1/podcasts/custom/abc', headers: {} },
        failing
      )
    ).rejects.toThrow();
    expect(networkStateOnline()).toBe(true);
  });

  it('always asks the network for sync downloads', async () => {
    const network = vi.fn().mockResolvedValue(ok({ modules: [1] }));
    await handle(officeConfig(), network);
    await handle(officeConfig({ headers: { [SYNC_HEADER]: '1' } }), network);
    expect(network).toHaveBeenCalledTimes(2); // the first load, then the sync despite the stored copy
  });

  it('does not keep audio that is still being prepared', async () => {
    const config = {
      method: 'get',
      url: '/api/v1/office/compline/2026-11-2?bible_translation=esv&include_audio_links=true',
      headers: {},
    };
    await handle(
      config,
      vi.fn().mockResolvedValue(ok({ audio: { status: 'preparing' } }, 200))
    );
    expect(await db.getAll('responses')).toHaveLength(0);
    await handle(
      config,
      vi.fn().mockResolvedValue(ok({ audio: { single_track: ['x.mp3'] } }))
    );
    expect(await db.getAll('responses')).toHaveLength(1);
  });

  it('leaves writes alone', async () => {
    const network = vi.fn().mockResolvedValue(ok({}));
    await handle(
      { method: 'post', url: '/api/v1/analytics/event', headers: {} },
      network
    );
    expect(await db.getAll('responses')).toHaveLength(0);
  });
});

function networkStateOnline() {
  return network.online;
}

describe('offline wording', () => {
  it('formats sizes and dates', () => {
    expect(formatBytes(0)).toBe('0 MB');
    expect(formatBytes(5 * 1024 * 1024)).toBe('5.0 MB');
    expect(formatBytes(50 * 1024 * 1024)).toBe('50 MB');
    const now = new Date(2026, 10, 2, 9);
    expect(friendlyDate('2026-11-02', now)).toBe('today');
    expect(friendlyDate('2026-11-03', now)).toBe('tomorrow');
    expect(friendlyDate('2026-11-05', now)).toBe('Thursday');
    expect(friendlyDate('2026-11-30', now)).toBe('Monday, November 30');
  });

  it('estimates more room for more days', () => {
    expect(estimateBytes({ days: 0 })).toBe(0);
    expect(estimateBytes({ days: 30 })).toBeGreaterThan(
      estimateBytes({ days: 7 })
    );
    expect(estimateBytes({ days: 7, family: true })).toBeGreaterThan(
      estimateBytes({ days: 7 })
    );
  });
});
