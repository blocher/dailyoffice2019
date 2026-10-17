import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { shallowMount } from '@vue/test-utils';
import AudioPlayer from '@/components/AudioPlayer.vue';
import { NativeAudioElement } from '@/helpers/nativeAudio';

// AudioPlayer driving the Android app's native player through
// NativeAudioElement, with the Capacitor plugin faked.
const URL = 'https://api.example.com/api/v1/audio_track/office.mp3?cid=abc';

const native = vi.hoisted(() => ({ plugin: null }));

vi.mock('@/helpers/storage', () => ({
  DynamicStorage: {
    getItem: vi.fn().mockResolvedValue(null),
    setItem: vi.fn().mockResolvedValue(),
  },
}));
vi.mock('@/helpers/nativeAudio', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    createAudioElement: (metadata) =>
      new actual.NativeAudioElement(native.plugin, metadata),
  };
});

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
    this.listeners.push(callback);
    return Promise.resolve({ remove: vi.fn() });
  }
  send(status) {
    this.status = { url: URL, duration: 1328, ...status };
    for (const callback of this.listeners) callback(this.status);
  }
  last(method) {
    return this.calls.filter(([name]) => name === method).at(-1)?.[1];
  }
  count(method) {
    return this.calls.filter(([name]) => name === method).length;
  }
}

let wrapper;
let plugin;
const flush = async () => {
  await Promise.resolve();
  await vi.advanceTimersByTimeAsync(0);
};
const mountPlayer = () => {
  wrapper = shallowMount(AudioPlayer, {
    props: {
      audio: [
        URL,
        '',
        [
          { name: 'Psalms', start_time: 208 },
          { name: 'First Reading', start_time: 334 },
        ],
        [],
      ],
      audioReady: true,
      office: 'morning_prayer',
      isEsvOrKjv: true,
      isWithinSevenDays: true,
    },
    global: { renderStubDefaultSlot: true, stubs: ['UiIcon'] },
  });
  return wrapper.vm;
};
const playingAt = (position) =>
  plugin.send({
    state: 'ready',
    position,
    buffered: position + 60,
    playWhenReady: true,
    isPlaying: true,
  });

beforeEach(() => {
  vi.useFakeTimers();
  plugin = new FakePlugin();
  native.plugin = plugin;
  Object.defineProperty(document, 'visibilityState', {
    configurable: true,
    value: 'visible',
  });
});
afterEach(() => {
  wrapper?.unmount();
  wrapper = null;
  vi.useRealTimers();
});

describe('AudioPlayer on the native Android player', () => {
  it('loads the office with its lock-screen title', async () => {
    const vm = mountPlayer();
    await flush();
    expect(vm.audioElement).toBeInstanceOf(NativeAudioElement);
    expect(plugin.last('setSource')).toMatchObject({
      url: URL,
      title: 'Morning Prayer',
      artist: 'The Daily Office',
      reuse: true,
    });
  });

  it('plays, follows the lock screen, and resumes', async () => {
    const vm = mountPlayer();
    await flush();
    plugin.send({ state: 'ready', position: 0 });
    vm.startAudio();
    await flush();
    expect(plugin.count('play')).toBe(1);
    playingAt(12);
    expect(vm.isPlaying).toBe(true);
    expect(vm.loading).toBe(false);

    plugin.send({ state: 'ready', position: 20, playWhenReady: false });
    expect(vm.isPlaying).toBe(false);
    expect(vm.isPaused).toBe(true);
    expect(vm.currentTime).toBe(20);

    playingAt(20);
    expect(vm.isPlaying).toBe(true);
  });

  it('jumps to a section through the native player', async () => {
    const vm = mountPlayer();
    await flush();
    plugin.send({ state: 'ready', position: 0 });
    vm.jumpToSection(334);
    await flush();
    expect(plugin.last('seekTo')).toEqual({ position: 333 });
    plugin.send({
      state: 'ready',
      position: 333,
      playWhenReady: true,
      isPlaying: true,
      event: 'seeked',
    });
    expect(vm.seeking).toBe(false);
    expect(vm.currentTime).toBeCloseTo(333);
  });

  it('reconnects in place when the player stalls with nothing arriving', async () => {
    const vm = mountPlayer();
    await flush();
    vm.startAudio();
    await flush();
    playingAt(307);
    plugin.send({
      state: 'buffering',
      position: 307,
      buffered: 307,
      playWhenReady: true,
    });
    expect(vm.loading).toBe(true);
    await vi.advanceTimersByTimeAsync(10000);
    expect(plugin.count('setSource')).toBe(2);
    expect(plugin.last('setSource').reuse).toBe(false);
    expect(plugin.count('play')).toBe(2);
    // The fresh connection reports the track; the player returns to its place.
    plugin.send({ state: 'ready', position: 0, playWhenReady: true });
    expect(plugin.last('seekTo').position).toBeCloseTo(307);
  });

  it('recovers from a player error during playback', async () => {
    const vm = mountPlayer();
    await flush();
    vm.startAudio();
    await flush();
    playingAt(500);
    plugin.send({ state: 'idle', error: 'Source error', position: 501 });
    expect(vm.playbackError).toContain('stopped loading');
    await vi.advanceTimersByTimeAsync(10000);
    expect(plugin.count('setSource')).toBe(2);
    plugin.send({ state: 'ready', position: 0, playWhenReady: true });
    expect(plugin.last('seekTo').position).toBeCloseTo(501);
  });

  it('rewinds when the office finishes', async () => {
    const vm = mountPlayer();
    await flush();
    vm.startAudio();
    await flush();
    playingAt(1320);
    plugin.send({ state: 'ended', position: 1328, playWhenReady: true });
    expect(vm.isPlaying).toBe(false);
    expect(vm.currentTime).toBe(0);
    expect(plugin.last('seekTo')).toEqual({ position: 0 });
  });

  it('stops the native player when leaving the office', async () => {
    mountPlayer();
    await flush();
    wrapper.unmount();
    wrapper = null;
    await flush();
    expect(plugin.calls.at(-1)[0]).toBe('stop');
  });
});
