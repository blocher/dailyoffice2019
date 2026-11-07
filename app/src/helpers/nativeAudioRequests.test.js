import { describe, it, expect, vi, beforeEach } from 'vitest';

const store = {};

vi.mock('./storage', () => ({
  DynamicStorage: {
    getItem: vi.fn(async (key) => (key in store ? store[key] : null)),
    setItem: vi.fn(async (key, value) => {
      store[key] = value;
      return value;
    }),
  },
}));

import { nativeAudioRequests } from './nativeAudioRequests';
import { apiDate, officeUrl } from '@/offline/urls';

// What the native side does with a template.
function fill(template, date, kind = '') {
  return template.replace('{date}', apiDate(date)).replace('{kind}', kind);
}

describe('nativeAudioRequests', () => {
  beforeEach(() => {
    for (const key of Object.keys(store)) delete store[key];
  });

  it('rebuilds exactly the address each office page asks for', async () => {
    const settings = {
      psalter: '30',
      language_style: 'traditional',
      bible_translation: 'kjv',
      reading_cycle: '2',
    };
    const extraCollects = { Compline: ['12', '34'], 'Morning Prayer': ['5'] };
    const requests = await nativeAudioRequests(settings, { extraCollects });
    const date = new Date(2026, 10, 7);
    for (const [serviceType, office] of [
      ['office', 'morning_prayer'],
      ['office', 'compline'],
      ['family', 'close_of_day_prayer'],
    ]) {
      expect(fill(requests.offices[`${serviceType}/${office}`], date)).toBe(
        officeUrl({ serviceType, office, date, settings, extraCollects }) +
          '&include_audio_links=true'
      );
    }
    expect(Object.keys(requests.offices)).toHaveLength(8);
  });

  it('adds the default translation where the page does', async () => {
    const requests = await nativeAudioRequests(
      { psalter: '60' },
      { extraCollects: null }
    );
    const url = fill(
      requests.offices['office/evening_prayer'],
      new Date(2026, 0, 2)
    );
    expect(url).toContain(
      '/office/evening_prayer/2026-1-2?psalter=60&bible_translation=esv&extra_collects='
    );
  });

  it('asks for readings the way the Readings page does', async () => {
    const requests = await nativeAudioRequests(
      { bible_translation: 'esv' },
      {
        extraCollects: null,
        readings: {
          translation: 'kjv',
          psalms: 'contemporary',
          style: 'unison',
          psalter: '60',
        },
      }
    );
    const date = new Date(2026, 10, 8);
    expect(fill(requests.readings, date, 'holy_eucharist')).toMatch(
      /api\/v1\/readings_audio\/holy_eucharist\/2026-11-8\?translation=kjv&psalms=contemporary&style=unison&psalter=60&position=0&include_audio_links=true$/
    );
  });

  it('reads the readings choices the page saved', async () => {
    store.readings_translation = 'esv';
    store.psalms_translation = 'traditional';
    store.psalm_style = 'whole_verse';
    store.psalter = '30';
    const requests = await nativeAudioRequests({}, { extraCollects: null });
    expect(requests.readings).toContain(
      '?translation=esv&psalms=traditional&style=whole_verse&psalter=30&position=0'
    );
  });
});
