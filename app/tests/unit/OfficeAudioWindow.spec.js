import { afterEach, describe, expect, it, vi } from 'vitest';
import Office from '@/views/Office.vue';

describe('office audio date window', () => {
  afterEach(() => vi.useRealTimers());

  it('includes all of the boundary days and excludes dates beyond them', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 9, 3, 18, 30));
    for (const [date, expected] of [
      [new Date(2026, 8, 30, 0, 0), true],
      [new Date(2026, 9, 12, 23, 59), true],
      [new Date(2026, 8, 29, 23, 59), false],
      [new Date(2026, 9, 13, 0, 0), false],
      [new Date(2050, 10, 17), false],
    ]) {
      expect(Office.computed.isWithinSevenDays.call({ calendarDate: date })).toBe(expected);
    }
  });

  it('does not request audio outside the window regardless of player visibility', async () => {
    for (const audioEnabled of [true, false]) {
      const get = vi.fn();
      const result = await Office.methods.setAudioLinks.call(
        { audioEnabled, isWithinSevenDays: false, $http: { get } }, '/office?test=1'
      );
      expect(result).toEqual([]);
      expect(get).not.toHaveBeenCalled();
    }
  });

  it('still fetches audio for an eligible office', async () => {
    const get = vi.fn().mockResolvedValue({ data: { audio: { single_track: [] } } });
    await Office.methods.setAudioLinks.call(
      { audioEnabled: true, isWithinSevenDays: true, $http: { get } }, '/office?test=1'
    );
    expect(get).toHaveBeenCalledWith('/office?test=1&include_audio_links=true');
  });
});
