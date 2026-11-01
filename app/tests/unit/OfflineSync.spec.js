import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const axios = vi.hoisted(() => ({ get: vi.fn(), post: vi.fn() }));
vi.mock('axios', () => ({ default: axios }));

import * as db from '@/offline/db';
import { setBrowserOnlineForTests } from '@/offline/network';
import { offlinePrefs } from '@/offline/preferences';
import { resetInvalidationsForTests } from '@/offline/staleness';
import { configureSync, requestSync, syncState } from '@/offline/sync';

const SETTINGS = { bible_translation: 'esv', psalter: '60' };

function isoOf(date) {
  const pad = (n) => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

const today = isoOf(new Date());
const trackUrl = (name) => `${window.location.origin}/api/v1/audio_track/${name}`;

async function storeTrack(name, date = today, office = 'morning_prayer') {
  await db.put('audio', {
    url: trackUrl(name),
    blob: new Blob(['mp3']),
    bytes: 3,
    date,
    office,
    savedAt: Date.now(),
  });
}

async function storedTracks() {
  return (await db.getAll('audio')).map((record) => record.url).sort();
}

describe('downloading office audio', () => {
  beforeEach(() => {
    db.resetForTests();
    resetInvalidationsForTests([]);
    setBrowserOnlineForTests(true);
    axios.get.mockReset();
    axios.post.mockReset().mockResolvedValue({ data: {} });
    configureSync({
      getContext: async () => ({ settings: SETTINGS, extraCollects: null }),
    });
    Object.assign(offlinePrefs, {
      days: 3,
      family: 'off',
      audio: true,
      audioOffices: ['morning_prayer'],
    });
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        headers: { get: () => null },
        blob: async () => new Blob(['mp3']),
      })
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    Object.assign(offlinePrefs, { days: null, audio: false });
  });

  // The API: every office and page answers; audio answers name a track per day.
  function answer({ audio } = {}) {
    axios.get.mockImplementation(async (url) => {
      if (url.includes('content_changes')) return { data: { version: 1 } };
      if (url.includes('include_audio_links')) return audio(url);
      return { data: {} };
    });
  }

  const trackFor = (url) => ({
    data: {
      audio: {
        single_track: [
          `/api/v1/audio_track/${url.match(/\d{4}-\d+-\d+/)[0]}.mp3`,
        ],
      },
    },
  });

  it('keeps the tracks it still wants and removes the others', async () => {
    await storeTrack('old.mp3', '2020-01-01');
    answer({ audio: trackFor });
    await requestSync('manual');
    const tracks = await storedTracks();
    expect(tracks).toHaveLength(2);
    expect(tracks).not.toContain(trackUrl('old.mp3'));
  });

  it('keeps stored audio when the connection drops mid-run', async () => {
    await storeTrack('today.mp3');
    axios.get.mockImplementation(async (url) => {
      if (url.includes('content_changes')) return { data: { version: 1 } };
      setBrowserOnlineForTests(false);
      throw Object.assign(new Error('Network Error'), { code: 'ERR_NETWORK' });
    });
    await requestSync('manual');
    expect(await storedTracks()).toEqual([trackUrl('today.mp3')]);
  });

  it("keeps an office's track when its answer can't be fetched or isn't ready", async () => {
    await storeTrack('today.mp3');
    answer({
      audio: async () => {
        throw Object.assign(new Error('timeout'), { code: 'ECONNABORTED' });
      },
    });
    await requestSync('manual');
    expect(await storedTracks()).toEqual([trackUrl('today.mp3')]);

    answer({ audio: async () => ({ data: { audio: { status: 'preparing' } } }) });
    await requestSync('manual');
    expect(await storedTracks()).toEqual([trackUrl('today.mp3')]);
    expect(syncState.audio.preparing).toBe(2);
  });
});
