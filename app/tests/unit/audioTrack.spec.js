import { describe, expect, it } from 'vitest';
import {
  beyondTrackEnd,
  endedEarly,
  freshTrackUrl,
  timelineEnd,
} from '@/helpers/audioTrack';

describe('audio track checks', () => {
  it('finds the end of the timeline from lines and sections', () => {
    expect(timelineEnd()).toBe(0);
    expect(
      timelineEnd(
        [{ start_time: 0 }, { start_time: 1200 }],
        [
          { start_time: 0, end_time: 30 },
          { start_time: 1300, end_time: 1444.5 },
        ]
      )
    ).toBe(1444.5);
    expect(timelineEnd([{ start_time: 80 }], [{ end_time: 'nope' }])).toBe(80);
  });

  it('flags playback that stops well before the timeline ends', () => {
    expect(endedEarly(1428, 1444)).toBe(true);
    expect(endedEarly(2451, 2618)).toBe(true);
    expect(endedEarly(1440, 1444)).toBe(false);
    expect(endedEarly(1444, 1444)).toBe(false);
    expect(endedEarly(NaN, 1444)).toBe(false);
    expect(endedEarly(600, 0)).toBe(false);
  });

  it('flags seek targets past the end of a known-length track', () => {
    expect(beyondTrackEnd(1500, 1428)).toBe(true);
    expect(beyondTrackEnd(1428.5, 1428)).toBe(false);
    expect(beyondTrackEnd(1500, NaN)).toBe(false);
    expect(beyondTrackEnd(1500, Infinity)).toBe(false);
    expect(beyondTrackEnd(1500, 0)).toBe(false);
  });

  it('adds a reload value while keeping existing query parameters', () => {
    expect(
      freshTrackUrl('https://api.example.com/api/v1/audio_track/a.mp3', 7)
    ).toBe('https://api.example.com/api/v1/audio_track/a.mp3?reload=7');
    const url = new window.URL(
      freshTrackUrl('https://api.example.com/t.mp3?cid=abc&reload=1', 9)
    );
    expect(url.searchParams.get('cid')).toBe('abc');
    expect(url.searchParams.get('reload')).toBe('9');
    expect(freshTrackUrl('')).toBe('');
  });
});
