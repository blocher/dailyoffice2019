import { beforeEach, describe, expect, it } from 'vitest';
import {
  PRAYER_REQUESTS_KEY,
  addPrayerRequest,
  prayerRequests,
  reloadPrayerRequests,
  removePrayerRequest,
  updatePrayerRequest,
} from './prayerRequests';

describe('prayerRequests', () => {
  beforeEach(() => {
    window.localStorage.clear();
    reloadPrayerRequests();
  });

  it('saves a trimmed request to localStorage', () => {
    addPrayerRequest({ name: '  Anna ', request: ' healing ' });
    const stored = JSON.parse(window.localStorage.getItem(PRAYER_REQUESTS_KEY));
    expect(stored).toHaveLength(1);
    expect(stored[0]).toMatchObject({ name: 'Anna', request: 'healing' });
    expect(prayerRequests.items).toHaveLength(1);
  });

  it('ignores an empty request', () => {
    expect(addPrayerRequest({ name: ' ', request: '' })).toBeNull();
    expect(prayerRequests.items).toHaveLength(0);
  });

  it('updates and removes requests', () => {
    const item = addPrayerRequest({ name: 'Ben', request: '' });
    updatePrayerRequest(item.id, { name: 'Ben', request: 'a new job' });
    reloadPrayerRequests();
    expect(prayerRequests.items[0].request).toBe('a new job');
    removePrayerRequest(item.id);
    reloadPrayerRequests();
    expect(prayerRequests.items).toHaveLength(0);
  });

  it('reads corrupt storage as empty', () => {
    window.localStorage.setItem(PRAYER_REQUESTS_KEY, '{nope');
    reloadPrayerRequests();
    expect(prayerRequests.items).toEqual([]);
  });
});
