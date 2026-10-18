import { afterEach, describe, expect, it, vi } from 'vitest';
import Office from '@/views/Office.vue';

describe('office audio date window', () => {
  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllEnvs();
  });

  it('skips eligible office and line audio requests when disabled by the environment', async () => {
    vi.stubEnv('VITE_FETCH_AUDIO_ON', 'false');
    const get = vi.fn();
    const post = vi.fn();
    const context = { isWithinSevenDays: true, $http: { get, post } };
    expect(Office.computed.audioLoadingEnabled()).toBe(false);
    expect(
      await Office.methods.setAudioLinks.call(context, '/office?test=1')
    ).toEqual([]);
    expect(
      await Office.methods.getAudioLinkForLine.call(context, {
        content: 'Test prayer',
        line_type: 'leader',
      })
    ).toBeNull();
    expect(get).not.toHaveBeenCalled();
    expect(post).not.toHaveBeenCalled();
  });

  it.each(['true', undefined])(
    'allows audio when the environment value is %s',
    (value) => {
      vi.stubEnv('VITE_FETCH_AUDIO_ON', value);
      expect(Office.computed.audioLoadingEnabled()).toBe(true);
    }
  );

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
      expect(
        Office.computed.isWithinSevenDays.call({ calendarDate: date })
      ).toBe(expected);
    }
  });

  it('does not request audio outside the window regardless of player visibility', async () => {
    for (const audioEnabled of [true, false]) {
      const get = vi.fn();
      const result = await Office.methods.setAudioLinks.call(
        { audioEnabled, isWithinSevenDays: false, $http: { get } },
        '/office?test=1'
      );
      expect(result).toEqual([]);
      expect(get).not.toHaveBeenCalled();
    }
  });

  it('still fetches audio for an eligible office', async () => {
    vi.stubEnv('VITE_FETCH_AUDIO_ON', 'true');
    const get = vi.fn().mockResolvedValue({
      data: { audio: { single_track: ['https://api.test/track.mp3', 'p'] } },
    });
    await Office.methods.setAudioLinks.call(
      { audioEnabled: true, isWithinSevenDays: true, $http: { get } },
      '/office?test=1'
    );
    expect(get).toHaveBeenCalledWith('/office?test=1&include_audio_links=true');
  });

  it('polls while the server prepares audio, then uses the ready track', async () => {
    vi.useFakeTimers();
    vi.stubEnv('VITE_FETCH_AUDIO_ON', 'true');
    const preparing = {
      status: 202,
      data: {
        audio: { status: 'preparing', retry_after: 5, single_track: [] },
      },
    };
    const get = vi
      .fn()
      .mockResolvedValueOnce(preparing)
      .mockResolvedValueOnce(preparing)
      .mockResolvedValueOnce({
        data: { audio: { single_track: ['https://api.test/track.mp3', 'p'] } },
      });
    // Track URLs are resolved against the API host the office came from.
    vi.stubEnv('VITE_API_URL', 'https://api.example/');
    const context = { isWithinSevenDays: true, $http: { get } };
    const result = Office.methods.setAudioLinks.call(context, '/office?a=1');
    await vi.advanceTimersByTimeAsync(4000);
    expect(get).toHaveBeenCalledTimes(1);
    await vi.advanceTimersByTimeAsync(1000);
    expect(get).toHaveBeenCalledTimes(2);
    await vi.advanceTimersByTimeAsync(5000);
    const [url, path] = await result;
    expect(url).toBe('https://api.example/track.mp3');
    expect(path).toBe('p');
    expect(get).toHaveBeenCalledTimes(3);
    expect(context.audioLinks).toEqual(await result);
  });

  it('stops polling once the office is closed', async () => {
    vi.useFakeTimers();
    vi.stubEnv('VITE_FETCH_AUDIO_ON', 'true');
    const get = vi.fn().mockResolvedValue({
      status: 202,
      data: { audio: { status: 'preparing', retry_after: 5 } },
    });
    const context = { isWithinSevenDays: true, $http: { get } };
    const result = Office.methods.setAudioLinks.call(context, '/office?a=1');
    await vi.advanceTimersByTimeAsync(0);
    Office.beforeUnmount.call(context);
    await vi.advanceTimersByTimeAsync(60000);
    expect(await result).toEqual([]);
    expect(get).toHaveBeenCalledTimes(1);
  });

  it('gives up after ten minutes of preparing', async () => {
    vi.useFakeTimers();
    vi.stubEnv('VITE_FETCH_AUDIO_ON', 'true');
    const get = vi.fn().mockResolvedValue({
      status: 202,
      data: { audio: { status: 'preparing', retry_after: 30 } },
    });
    const result = Office.methods.setAudioLinks.call(
      { isWithinSevenDays: true, $http: { get } },
      '/office?a=1'
    );
    await vi.advanceTimersByTimeAsync(11 * 60 * 1000);
    expect(await result).toEqual([]);
    expect(get.mock.calls.length).toBeLessThanOrEqual(22);
  });
});
