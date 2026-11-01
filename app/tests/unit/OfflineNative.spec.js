import { beforeEach, describe, expect, it, vi } from 'vitest';

const plugin = vi.hoisted(() => ({
  schedule: vi.fn(),
  drain: vi.fn(),
  ack: vi.fn(),
}));

vi.mock('@capacitor/core', () => ({
  Capacitor: {
    isNativePlatform: () => true,
    isPluginAvailable: (name) => name === 'OfflineSync',
    getPlatform: () => 'ios',
    convertFileSrc: (uri) => uri,
  },
  registerPlugin: () => plugin,
}));

import * as db from '@/offline/db';
import {
  readEntry,
  resetStoredIndex,
  storeEntry,
} from '@/offline/cacheAdapter';
import {
  currentInvalidations,
  mergeInvalidations,
  resetInvalidationsForTests,
} from '@/offline/staleness';
import {
  drainInbox,
  nativeSyncState,
  scheduleBackground,
} from '@/offline/native';

const KEY = 'office/morning_prayer/2026-11-2?bible_translation=esv';
const URL = `https://api.example.com/api/v1/${KEY}`;

function entry(key, fetchedAt, body = { ok: key }) {
  return {
    key,
    url: `https://api.example.com/api/v1/${key}`,
    kind: 'office',
    date: '2026-11-02',
    profile: 'abc',
    fetchedAt,
    body: JSON.stringify(body),
  };
}

function inbox(entries, extra = {}) {
  return {
    entries,
    remaining: 0,
    contentVersion: 0,
    invalidations: [],
    audio: [],
    ...extra,
  };
}

describe('merging content changes', () => {
  beforeEach(() => {
    db.resetForTests();
    resetStoredIndex();
    resetInvalidationsForTests([]);
  });

  it('adds new changes in order and skips ones already known', async () => {
    resetInvalidationsForTests([
      {
        at: 200,
        all: false,
        urgent: false,
        dates: [['2026-11-02', '2026-11-02']],
      },
    ]);
    const added = await mergeInvalidations([
      {
        at: 200,
        all: false,
        urgent: false,
        dates: [['2026-11-02', '2026-11-02']],
      },
      {
        at: 100,
        all: true,
        urgent: false,
        dates: [['2026-12-25', '2026-12-25']],
      },
      { at: 300, all: false, urgent: false, dates: [] },
      null,
    ]);
    expect(added).toBe(1);
    expect((await currentInvalidations()).map((i) => i.at)).toEqual([100, 200]);
    // An every-date change keeps its dated ranges: those dates are urgent.
    expect((await currentInvalidations())[0].dates).toEqual([
      ['2026-12-25', '2026-12-25'],
    ]);
    expect(await db.meta.get('invalidations')).toHaveLength(2);
  });
});

describe('the background inbox', () => {
  beforeEach(() => {
    db.resetForTests();
    resetStoredIndex();
    resetInvalidationsForTests([]);
    plugin.schedule.mockReset();
    plugin.drain.mockReset();
    plugin.ack.mockReset().mockResolvedValue(undefined);
  });

  it('stores each entry with its download time, then lets it go', async () => {
    plugin.drain.mockResolvedValueOnce(inbox([entry(KEY, 1234)]));
    expect(await drainInbox()).toBe(1);
    const record = await readEntry(KEY);
    expect(record).toMatchObject({
      key: KEY,
      kind: 'office',
      date: '2026-11-02',
      profile: 'abc',
      fetchedAt: 1234,
      data: { ok: KEY },
    });
    expect(plugin.drain).toHaveBeenCalledWith({ limit: 20 });
    expect(plugin.ack).toHaveBeenCalledWith({
      keys: [KEY],
      invalidationsThrough: 0,
      audio: [],
    });
    expect(nativeSyncState.drained).toBe(1);
  });

  it('drains in batches until the inbox is empty', async () => {
    plugin.drain
      .mockResolvedValueOnce(
        inbox([entry('calendar/2026-11-2', 1)], { remaining: 1 })
      )
      .mockResolvedValueOnce(inbox([entry('calendar/2026-11-3', 2)]));
    expect(await drainInbox()).toBe(2);
    expect(plugin.drain).toHaveBeenCalledTimes(2);
    expect(plugin.ack).toHaveBeenCalledTimes(2);
  });

  it('keeps a newer copy already in storage, but still lets the entry go', async () => {
    await storeEntry(
      KEY,
      { kind: 'office', date: '2026-11-02' },
      URL,
      { newer: true },
      {
        fetchedAt: 5000,
      }
    );
    plugin.drain.mockResolvedValueOnce(inbox([entry(KEY, 4000)]));
    expect(await drainInbox()).toBe(0);
    expect((await readEntry(KEY)).data).toEqual({ newer: true });
    expect(plugin.ack.mock.calls[0][0].keys).toEqual([KEY]);
  });

  it('lets go of entries that are not answers', async () => {
    plugin.drain.mockResolvedValueOnce(
      inbox([{ ...entry(KEY, 1), body: 'not json' }])
    );
    expect(await drainInbox()).toBe(0);
    expect(await readEntry(KEY)).toBeNull();
    expect(plugin.ack.mock.calls[0][0].keys).toEqual([KEY]);
  });

  it('lets go of audio answers whose track is still being prepared', async () => {
    const audioKey = `${KEY}&include_audio_links=true`;
    plugin.drain.mockResolvedValueOnce(
      inbox([
        {
          ...entry(audioKey, 1, { audio: { status: 'preparing' } }),
          kind: 'audio',
        },
      ])
    );
    expect(await drainInbox()).toBe(0);
    expect(await readEntry(audioKey)).toBeNull();
    expect(plugin.ack.mock.calls[0][0].keys).toEqual([audioKey]);
  });

  it('leaves entries in the inbox when storage is full', async () => {
    const put = vi
      .spyOn(db, 'put')
      .mockRejectedValueOnce(
        Object.assign(new Error('full'), { name: 'QuotaExceededError' })
      );
    plugin.drain.mockResolvedValueOnce(
      inbox([entry(KEY, 1), entry('calendar/2026-11-2', 2)], { remaining: 3 })
    );
    expect(await drainInbox()).toBe(0);
    expect(plugin.drain).toHaveBeenCalledTimes(1);
    expect(plugin.ack.mock.calls[0][0].keys).toEqual([]);
    put.mockRestore();
  });

  it('merges the content version, changes, and audio the task learned', async () => {
    await db.meta.set('contentVersion', 7);
    const change = {
      at: 900,
      all: false,
      urgent: true,
      dates: [['2026-11-02', '2026-11-04']],
    };
    const track = {
      url: 'https://api.example.com/audio/mp.mp3',
      path: 'offline-audio/abc.mp3',
      bytes: 42,
      date: '2026-11-02',
      office: 'morning_prayer',
      savedAt: 950,
    };
    plugin.drain.mockResolvedValueOnce(
      inbox([], { contentVersion: 9, invalidations: [change], audio: [track] })
    );
    await drainInbox();
    expect(await db.meta.get('contentVersion')).toBe(9);
    expect(await currentInvalidations()).toEqual([change]);
    expect(await db.get('audio', track.url)).toEqual(track);
    expect(plugin.ack).toHaveBeenCalledWith({
      keys: [],
      invalidationsThrough: 900,
      audio: [track.url],
    });
  });

  it('never lowers the content version', async () => {
    await db.meta.set('contentVersion', 12);
    plugin.drain.mockResolvedValueOnce(inbox([], { contentVersion: 9 }));
    await drainInbox();
    expect(await db.meta.get('contentVersion')).toBe(12);
  });

  it('never rejects', async () => {
    plugin.drain.mockRejectedValueOnce(new Error('bridge gone'));
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    await expect(drainInbox()).resolves.toBe(0);
    warn.mockRestore();
  });
});

describe('scheduling background downloads', () => {
  beforeEach(() => {
    db.resetForTests();
    resetStoredIndex();
    resetInvalidationsForTests([]);
    plugin.schedule.mockReset().mockResolvedValue({ scheduled: true });
  });

  it('hands over the plan, the changes, and when each answer was stored', async () => {
    const change = { at: 10, all: true, urgent: false, dates: [] };
    resetInvalidationsForTests([change]);
    await db.meta.set('contentVersion', 4);
    await storeEntry(
      KEY,
      { kind: 'office', date: '2026-11-02' },
      URL,
      {},
      { fetchedAt: 77 }
    );
    const plan = {
      createdAt: 1,
      days: 3,
      apiBase: 'https://api.example.com/',
      tasks: [
        { url: URL, key: KEY, kind: 'office', date: '2026-11-02' },
        {
          url: 'x',
          key: 'calendar/2026-11-3',
          kind: 'day',
          date: '2026-11-03',
        },
      ],
    };
    expect(await scheduleBackground(plan)).toBe(true);
    expect(plugin.schedule).toHaveBeenCalledWith({
      plan,
      contentVersion: 4,
      invalidations: [change],
      fetched: { [KEY]: 77 },
      audio: { enabled: false, tasks: [] },
    });
    expect(nativeSyncState.scheduled).toBe(true);
  });

  it('describes the audio offices wanted', async () => {
    const audioUrl = `/api/v1/office/morning_prayer/2026-11-2?bible_translation=esv&include_audio_links=true`;
    await scheduleBackground(
      { tasks: [{ url: URL, key: KEY, kind: 'office', date: '2026-11-02' }] },
      {
        audio: [
          { url: audioUrl, date: '2026-11-02', office: 'morning_prayer' },
        ],
      }
    );
    const { audio } = plugin.schedule.mock.calls[0][0];
    expect(audio.enabled).toBe(true);
    expect(audio.tasks[0]).toMatchObject({
      url: audioUrl,
      key: 'office/morning_prayer/2026-11-2?bible_translation=esv&include_audio_links=true',
      kind: 'audio',
      date: '2026-11-02',
      office: 'morning_prayer',
      track: null,
    });
  });

  it('stops the background task when there is nothing to download', async () => {
    plugin.schedule.mockResolvedValue({ scheduled: false });
    expect(await scheduleBackground(null)).toBe(false);
    expect(plugin.schedule.mock.calls[0][0].plan).toEqual({ tasks: [] });
    expect(nativeSyncState.scheduled).toBe(false);
  });
});
