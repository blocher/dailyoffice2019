import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  createAudioElement,
  NativeAudioElement,
} from '@/helpers/nativeAudio';

const URL = 'https://api.example.com/api/v1/audio_track/office.mp3?cid=abc';

// The NativeAudio Capacitor plugin: records calls, and lets a test push the
// `status` events the Android player would send.
class FakePlugin {
  constructor() {
    this.calls = [];
    this.listeners = [];
    this.status = { url: URL, state: 'idle', position: 0 };
    for (const method of [
      'setSource',
      'play',
      'pause',
      'seekTo',
      'setRate',
      'stop',
    ]) {
      this[method] = vi.fn((options) => {
        this.calls.push([method, options]);
        return Promise.resolve(this.status);
      });
    }
  }
  addListener(event, callback) {
    const handle = { remove: vi.fn() };
    this.listeners.push({ callback, handle });
    return Promise.resolve(handle);
  }
  send(status) {
    this.status = { url: URL, ...status };
    for (const { callback } of this.listeners) callback(this.status);
  }
}

let plugin;
let element;
let events;
let clock;

const record = (target) => {
  const names = [
    'loadedmetadata',
    'durationchange',
    'canplay',
    'canplaythrough',
    'play',
    'playing',
    'pause',
    'waiting',
    'seeking',
    'seeked',
    'timeupdate',
    'progress',
    'ratechange',
    'ended',
    'error',
  ];
  for (const name of names) {
    target.addEventListener(name, () => events.push(name));
  }
};
// Let pending command promises settle.
const settle = () => new Promise((resolve) => setTimeout(resolve, 0));

beforeEach(() => {
  clock = 1000;
  vi.spyOn(window.performance, 'now').mockImplementation(() => clock);
  plugin = new FakePlugin();
  element = new NativeAudioElement(plugin, {
    title: 'Morning Prayer',
    artist: 'The Daily Office',
  });
  events = [];
  record(element);
  element.src = URL;
});
afterEach(() => {
  vi.restoreAllMocks();
});

const ready = (extra = {}) =>
  plugin.send({
    state: 'ready',
    duration: 1328,
    buffered: 120,
    position: 0,
    playWhenReady: false,
    isPlaying: false,
    ...extra,
  });

describe('createAudioElement', () => {
  it('uses a real Audio element outside the Android app', () => {
    const audio = createAudioElement({ title: 'Compline' });
    expect(audio).toBeInstanceOf(window.HTMLAudioElement);
  });
});

describe('NativeAudioElement', () => {
  it('starts like an empty media element', () => {
    expect(element.paused).toBe(true);
    expect(element.ended).toBe(false);
    expect(element.readyState).toBe(0);
    expect(Number.isNaN(element.duration)).toBe(true);
    expect(element.seekable.length).toBe(0);
  });

  it('loads the source with lock-screen metadata, reusing only the first time', () => {
    element.load();
    expect(plugin.calls[0]).toEqual([
      'setSource',
      {
        url: URL,
        title: 'Morning Prayer',
        artist: 'The Daily Office',
        rate: 1,
        reuse: true,
      },
    ]);
    element.load();
    expect(plugin.calls[1][1].reuse).toBe(false);
  });

  it('reports metadata and readiness as media events', () => {
    element.load();
    ready();
    expect(events).toEqual([
      'durationchange',
      'loadedmetadata',
      'progress',
      'canplay',
      'canplaythrough',
    ]);
    expect(element.duration).toBe(1328);
    expect(element.readyState).toBe(4);
    expect(element.seekable.end(0)).toBe(1328);
    expect(element.buffered.end(0)).toBe(120);
  });

  it('plays, and keeps time smoothly between status reports', async () => {
    element.load();
    ready();
    events = [];
    const played = element.play();
    expect(element.paused).toBe(false);
    expect(events).toEqual(['play']);
    await expect(played).resolves.toBeUndefined();
    plugin.send({
      state: 'ready',
      duration: 1328,
      position: 10,
      playWhenReady: true,
      isPlaying: true,
    });
    expect(events).toContain('playing');
    clock += 500;
    expect(element.currentTime).toBeCloseTo(10.5);
    element.playbackRate = 2;
    expect(plugin.calls.at(-1)).toEqual(['setRate', { rate: 2 }]);
    clock += 500;
    expect(element.currentTime).toBeCloseTo(11.5);
  });

  it('signals waiting while the player buffers', () => {
    element.load();
    element.play();
    expect(events).toContain('waiting');
    events = [];
    plugin.send({ state: 'ready', duration: 1328, playWhenReady: true, isPlaying: true });
    plugin.send({ state: 'buffering', duration: 1328, position: 30, playWhenReady: true });
    expect(events).toContain('waiting');
    expect(element.readyState).toBe(2);
    events = [];
    plugin.send({ state: 'buffering', duration: 1328, position: 30, playWhenReady: true });
    expect(events).not.toContain('waiting');
  });

  it('follows play and pause from the lock screen', async () => {
    element.load();
    await settle();
    ready({ playWhenReady: true, isPlaying: true, position: 5 });
    expect(element.paused).toBe(false);
    expect(events).toContain('play');
    expect(events).toContain('playing');
    events = [];
    ready({ playWhenReady: false, isPlaying: false, position: 6 });
    expect(element.paused).toBe(true);
    expect(events).toContain('pause');
    expect(element.currentTime).toBe(6);
  });

  it('does not let a status sent before play() undo it', async () => {
    element.load();
    await settle();
    ready();
    let resolvePlay;
    plugin.play.mockImplementation(
      () => new Promise((resolve) => (resolvePlay = resolve))
    );
    element.play();
    ready({ playWhenReady: false });
    expect(element.paused).toBe(false);
    resolvePlay({ url: URL, state: 'ready', duration: 1328, playWhenReady: true });
    await settle();
    expect(element.paused).toBe(false);
  });

  it('pauses at once and tells the player', () => {
    element.load();
    ready();
    element.play();
    events = [];
    element.pause();
    expect(element.paused).toBe(true);
    expect(events).toEqual(['timeupdate', 'pause']);
    expect(plugin.calls.at(-1)[0]).toBe('pause');
  });

  it('holds a seek target until the player reaches it', () => {
    element.load();
    ready();
    element.currentTime = 600;
    expect(plugin.calls.at(-1)).toEqual(['seekTo', { position: 600 }]);
    expect(element.currentTime).toBe(600);
    expect(events).toContain('seeking');
    ready({ position: 3 });
    expect(element.currentTime).toBe(600);
    events = [];
    ready({ position: 600.2, event: 'seeked' });
    expect(events).toContain('seeked');
    expect(element.currentTime).toBeCloseTo(600.2);
  });

  it('gives up on a seek target the player never reports', () => {
    element.load();
    ready();
    element.currentTime = 600;
    clock += 5000;
    ready({ position: 42 });
    expect(element.currentTime).toBe(42);
  });

  it('clamps seeks to the track', () => {
    element.load();
    ready();
    element.currentTime = 5000;
    expect(element.currentTime).toBe(1328);
    element.currentTime = -4;
    expect(element.currentTime).toBe(0);
    element.currentTime = NaN;
    expect(element.currentTime).toBe(0);
  });

  it('ends like a media element', () => {
    element.load();
    ready();
    element.play();
    events = [];
    plugin.send({ state: 'ended', duration: 1328, position: 1328, playWhenReady: true });
    expect(events).toEqual(['timeupdate', 'pause', 'ended']);
    expect(element.ended).toBe(true);
    expect(element.paused).toBe(true);
    element.play();
    expect(plugin.calls.some(([m, o]) => m === 'seekTo' && o.position === 0)).toBe(true);
  });

  it('reports a player error once as a network error', () => {
    element.load();
    ready({ playWhenReady: true, isPlaying: true, position: 300 });
    events = [];
    plugin.send({ state: 'idle', error: 'Source error', position: 301 });
    plugin.send({ state: 'idle', error: 'Source error', position: 301 });
    expect(events).toEqual(['error']);
    expect(element.error.code).toBe(2);
    expect(element.currentTime).toBe(301);
    element.load();
    expect(element.error).toBe(null);
  });

  it('ignores status from another track or from no track', () => {
    element.load();
    plugin.send({ url: 'https://other/track.mp3', state: 'ready', duration: 99 });
    expect(Number.isNaN(element.duration)).toBe(true);
    ready({ position: 120 });
    plugin.send({ url: undefined, state: 'idle', position: 0 });
    expect(element.currentTime).toBe(120);
  });

  it('stops the player and its listener when the source is removed', async () => {
    element.load();
    await settle();
    const { handle } = plugin.listeners[0];
    element.removeAttribute('src');
    element.load();
    await settle();
    expect(plugin.calls.at(-1)[0]).toBe('stop');
    expect(handle.remove).toHaveBeenCalled();
    ready();
    expect(Number.isNaN(element.duration)).toBe(true);
  });

  it('rejects play() when the player cannot start', async () => {
    element.load();
    plugin.play.mockRejectedValue(new Error('no session'));
    await expect(element.play()).rejects.toThrow('no session');
  });

  it('survives a plugin method that throws', async () => {
    plugin.seekTo.mockImplementation(() => {
      throw new Error('bridge gone');
    });
    element.load();
    ready();
    expect(() => {
      element.currentTime = 10;
    }).not.toThrow();
    await settle();
    expect(element.pendingCommands).toBe(0);
  });
});
