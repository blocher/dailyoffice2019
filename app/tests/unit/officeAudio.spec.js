import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { fetchAudioTrack } from '@/helpers/officeAudio';

const TRACK = [
  'https://api.example.com/api/v1/audio_track/office.mp3',
  '/media/office.mp3',
  [{ name: 'Opening', start_time: 0 }],
  [],
  [],
];
const ok = (audio) => Promise.resolve({ data: { audio } });
const fail = (status) =>
  Promise.reject(
    Object.assign(new Error('request failed'), {
      response: status ? { status } : undefined,
    })
  );

beforeEach(() => {
  vi.useFakeTimers();
});
afterEach(() => {
  vi.useRealTimers();
});

describe('fetchAudioTrack', () => {
  it('returns the track with one URL for every listener', async () => {
    const http = { get: vi.fn(() => ok({ single_track: [...TRACK] })) };
    const track = await fetchAudioTrack(http, '/office?include_audio_links=true');
    // No per-client query, so Cloudflare can answer from its cache.
    expect(track[0]).toMatch(/\/api\/v1\/audio_track\/office\.mp3$/);
    expect(http.get).toHaveBeenCalledOnce();
  });

  it('polls while the server prepares the audio', async () => {
    const http = {
      get: vi
        .fn()
        .mockReturnValueOnce(ok({ status: 'preparing', retry_after: 5 }))
        .mockReturnValue(ok({ single_track: [...TRACK] })),
    };
    const result = fetchAudioTrack(http, '/office');
    await vi.advanceTimersByTimeAsync(5000);
    expect((await result).length).toBe(5);
  });

  it.each([
    ['a dropped connection', () => fail()],
    ['a server error', () => fail(503)],
    ['an answer with no track', () => ok({ single_track: [] })],
  ])('asks again after %s', async (label, failure) => {
    const http = {
      get: vi
        .fn()
        .mockImplementationOnce(failure)
        .mockImplementationOnce(failure)
        .mockReturnValue(ok({ single_track: [...TRACK] })),
    };
    const result = fetchAudioTrack(http, '/office');
    await vi.advanceTimersByTimeAsync(3000 + 10000);
    expect((await result).length).toBe(5);
    expect(http.get).toHaveBeenCalledTimes(3);
  });

  it('gives up after the last retry', async () => {
    const http = { get: vi.fn(() => fail(502)) };
    const result = fetchAudioTrack(http, '/office');
    await vi.advanceTimersByTimeAsync(3000 + 10000 + 30000);
    expect(await result).toEqual([]);
    expect(http.get).toHaveBeenCalledTimes(4);
  });

  it('does not retry a request the server rejected', async () => {
    const http = { get: vi.fn(() => fail(404)) };
    expect(await fetchAudioTrack(http, '/office')).toEqual([]);
    expect(http.get).toHaveBeenCalledOnce();
  });

  it('stops retrying once the page is left', async () => {
    let stopped = false;
    const http = { get: vi.fn(() => fail()) };
    const result = fetchAudioTrack(http, '/office', () => stopped);
    stopped = true;
    await vi.advanceTimersByTimeAsync(3000);
    expect(await result).toEqual([]);
    expect(http.get).toHaveBeenCalledOnce();
  });
});
