import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { shallowMount } from '@vue/test-utils';
import AudioPlayer from '@/components/AudioPlayer.vue';
import { DynamicStorage } from '@/helpers/storage';

vi.mock('@/helpers/storage', () => ({
  DynamicStorage: {
    getItem: vi.fn().mockResolvedValue(null),
    setItem: vi.fn().mockResolvedValue(),
  },
}));

class FakeAudio extends window.EventTarget {
  constructor() {
    super();
    this.currentTime = 0;
    this.duration = 600;
    this.playbackRate = 1;
    this.readyState = 4;
    this.paused = true;
    this.ended = false;
    this.seekable = { length: 1, start: () => 0, end: () => this.duration };
    this.load = vi.fn();
    this.play = vi.fn(() => Promise.resolve());
    this.pause = vi.fn(() => {
      this.paused = true;
      this.emit('pause');
    });
    this.removeAttribute = vi.fn();
  }
  emit(name) {
    this.dispatchEvent(new window.Event(name));
  }
}

let audio;
let wrapper;
let actions;
let mediaSession;
const mountPlayer = () => {
  wrapper = shallowMount(AudioPlayer, {
    props: {
      audio: [
        'https://example.com/office.mp3',
        '',
        [{ name: 'Reading', start_time: 60 }],
        [],
      ],
      audioReady: true,
      office: 'morning_prayer',
      isEsvOrKjv: true,
      isWithinSevenDays: true,
    },
    global: {
      renderStubDefaultSlot: true,
      stubs: ['UiIcon'],
    },
  });
  return wrapper.vm;
};
beforeEach(() => {
  DynamicStorage.getItem.mockResolvedValue(null);
  DynamicStorage.setItem.mockResolvedValue();
  audio = new FakeAudio();
  vi.stubGlobal(
    'Audio',
    vi.fn(function () {
      return audio;
    })
  );
  actions = {};
  mediaSession = {
    setActionHandler: vi.fn((name, callback) => {
      actions[name] = callback;
    }),
    setPositionState: vi.fn(),
  };
  Object.defineProperty(navigator, 'mediaSession', {
    configurable: true,
    value: mediaSession,
  });
  Object.defineProperty(document, 'visibilityState', {
    configurable: true,
    value: 'visible',
  });
});
afterEach(() => {
  wrapper?.unmount();
  wrapper = null;
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  delete navigator.mediaSession;
});

describe('AudioPlayer playback lifecycle', () => {
  it.each([true, false])(
    'preserves media position and lifecycle when playing=%s during mode changes',
    async (playing) => {
      const vm = mountPlayer();
      audio.currentTime = 307;
      if (playing) {
        vm.startAudio();
        audio.paused = false;
        audio.emit('playing');
      } else {
        audio.emit('pause');
      }
      const plays = audio.play.mock.calls.length;
      const pauses = audio.pause.mock.calls.length;
      const loads = audio.load.mock.calls.length;
      for (const mode of ['sentence', 'off', 'word', 'off', 'sentence']) {
        vm.changeHighlightMode(mode);
        await vm.$nextTick();
        expect(audio.currentTime).toBe(307);
        expect(vm.isPlaying).toBe(playing);
        expect(audio.play).toHaveBeenCalledTimes(plays);
        expect(audio.pause).toHaveBeenCalledTimes(pauses);
        expect(audio.load).toHaveBeenCalledTimes(loads);
      }
      vm.seekTo(100);
      expect(audio.currentTime).toBe(100);
      expect(vm.highlightMode).toBe('sentence');
    }
  );

  it('sets preload and waits for real playback state', () => {
    const vm = mountPlayer();
    expect(audio.preload).toBe('auto');
    vm.startAudio();
    expect(vm.isPlaying).toBe(false);
    audio.paused = false;
    audio.emit('playing');
    expect(vm.isPlaying).toBe(true);
    expect(vm.loading).toBe(false);
    expect(mediaSession.playbackState).toBe('playing');
  });
  it('catches rejected play and displays retry feedback', async () => {
    audio.play.mockRejectedValue(
      Object.assign(new Error('blocked'), { name: 'NotAllowedError' })
    );
    const vm = mountPlayer();
    vm.startAudio();
    await Promise.resolve();
    await vm.$nextTick();
    expect(vm.isPlaying).toBe(false);
    expect(vm.loading).toBe(false);
    expect(wrapper.text()).toContain('Playback was interrupted');
  });
  it('respects OS pauses when foregrounded or buffered', () => {
    const vm = mountPlayer();
    vm.startAudio();
    audio.paused = false;
    audio.emit('playing');
    audio.currentTime = 307;
    audio.paused = true;
    audio.emit('pause');
    document.dispatchEvent(new window.Event('visibilitychange'));
    audio.emit('canplay');
    expect(vm.isPlaying).toBe(false);
    expect(vm.isPaused).toBe(true);
    expect(audio.play).toHaveBeenCalledTimes(1);
    expect(vm.currentTime).toBe(307);
  });
  it('distinguishes buffering and clears it when playback resumes', () => {
    const vm = mountPlayer();
    vm.startAudio();
    audio.emit('playing');
    audio.emit('waiting');
    expect(vm.loading).toBe(true);
    audio.emit('stalled');
    expect(vm.playbackError).toContain('buffering');
    audio.emit('playing');
    expect(vm.playbackError).toBe('');
    expect(vm.loading).toBe(false);
  });
  it('restores position after explicit retry', () => {
    const vm = mountPlayer();
    audio.currentTime = 307;
    audio.emit('error');
    expect(vm.playbackError).toContain('stopped loading');
    audio.load.mockImplementation(() => {
      audio.currentTime = 0;
    });
    vm.retryAudio();
    expect(audio.load).toHaveBeenCalledTimes(2);
    audio.emit('loadedmetadata');
    expect(audio.currentTime).toBe(307);
    expect(audio.play).toHaveBeenCalledTimes(1);
  });
  it('preserves resume position through repeated network failures', () => {
    const vm = mountPlayer();
    audio.currentTime = 307;
    audio.load.mockImplementation(() => {
      audio.currentTime = 0;
    });
    vm.retryAudio();
    audio.emit('timeupdate');
    audio.emit('error');
    vm.retryAudio();
    audio.emit('loadedmetadata');
    expect(audio.currentTime).toBe(307);
  });
  it('lets a new seek replace an older retry target', () => {
    const vm = mountPlayer();
    audio.currentTime = 307;
    vm.retryAudio();
    vm.seekTo(100);
    audio.emit('loadedmetadata');
    expect(audio.currentTime).toBe(100);
  });
  it('retries a clamped seek once more data arrives', () => {
    const vm = mountPlayer();
    let position = 0;
    let bufferedEnd = 20;
    Object.defineProperty(audio, 'currentTime', {
      get: () => position,
      set: (value) => {
        position = Math.min(value, bufferedEnd);
      },
    });
    vm.seekTo(120);
    expect(audio.currentTime).toBe(20);
    bufferedEnd = 600;
    audio.emit('progress');
    expect(audio.currentTime).toBe(120);
    expect(vm.pendingResumeTime).toBe(null);
  });
  it('does not let rejected pending play override explicit pause', async () => {
    let reject;
    audio.play.mockReturnValue(
      new Promise((_, fail) => {
        reject = fail;
      })
    );
    const vm = mountPlayer();
    vm.startAudio();
    vm.pauseAudio();
    reject(new Error('aborted'));
    await Promise.resolve();
    expect(vm.playbackError).toBe('');
    expect(vm.isPlaying).toBe(false);
  });
  it('ignores stale rejection after a new play attempt', async () => {
    let reject;
    audio.play.mockReturnValueOnce(
      new Promise((_, fail) => {
        reject = fail;
      })
    );
    const vm = mountPlayer();
    vm.startAudio();
    vm.pauseAudio();
    vm.startAudio();
    audio.emit('playing');
    reject(new Error('old attempt'));
    await Promise.resolve();
    expect(vm.isPlaying).toBe(true);
    expect(vm.playbackError).toBe('');
  });
  it('keeps an early chapter seek until metadata is available', () => {
    audio.duration = NaN;
    const vm = mountPlayer();
    vm.currentTrackSegment = 120;
    vm.handleTrackSegmentChange();
    expect(audio.currentTime).toBe(0);
    audio.duration = 600;
    audio.emit('loadedmetadata');
    expect(audio.currentTime).toBe(119);
  });
  it('preserves analytics once per actual playback session', () => {
    const vm = mountPlayer();
    vm.startAudio();
    expect(wrapper.emitted('audio-play')).toBeUndefined();
    audio.emit('playing');
    vm.pauseAudio();
    vm.startAudio();
    audio.emit('playing');
    expect(wrapper.emitted('audio-play')).toHaveLength(1);
  });
  it('preserves chapter lead-in and seekable-range gating', () => {
    const vm = mountPlayer();
    let seekableEnd = 20;
    audio.seekable.end = () => seekableEnd;
    vm.currentTrackSegment = 120;
    vm.handleTrackSegmentChange();
    expect(audio.currentTime).toBe(0);
    seekableEnd = 600;
    audio.emit('progress');
    expect(audio.currentTime).toBe(119);
    audio.emit('seeked');
    expect(vm.cancelTrackSeek).toBe(null);
  });
  it('cancels pending chapter seek on user pause', () => {
    const vm = mountPlayer();
    audio.seekable.end = () => 20;
    vm.currentTrackSegment = 120;
    vm.handleTrackSegmentChange();
    vm.pauseAudio();
    audio.seekable.end = () => 600;
    audio.emit('progress');
    expect(audio.currentTime).toBe(0);
    expect(vm.cancelTrackSeek).toBe(null);
  });
  it('lets lock-screen seek replace pending chapter jump', () => {
    const vm = mountPlayer();
    audio.seekable.end = () => 20;
    vm.currentTrackSegment = 120;
    vm.handleTrackSegmentChange();
    actions.seekto({ seekTime: 50 });
    audio.seekable.end = () => 600;
    audio.emit('progress');
    expect(audio.currentTime).toBe(50);
    expect(vm.cancelTrackSeek).toBe(null);
  });
  it('supports OS controls and bounds seeks to track duration', () => {
    const vm = mountPlayer();
    actions.play();
    expect(audio.play).toHaveBeenCalledTimes(1);
    actions.seekto({ seekTime: 1000 });
    expect(audio.currentTime).toBeCloseTo(599.95);
    actions.seekbackward({ seekOffset: 10 });
    expect(audio.currentTime).toBeCloseTo(589.95);
    actions.pause();
    expect(vm.isPlaying).toBe(false);
    actions.stop();
    expect(audio.currentTime).toBe(0);
  });
  it('tolerates unsupported actions and invalid duration', () => {
    mediaSession.setActionHandler.mockImplementation(() => {
      throw new Error('unsupported');
    });
    audio.duration = Infinity;
    const vm = mountPlayer();
    audio.emit('loadedmetadata');
    expect(vm.duration).toBe(0);
    vm.seekTo(5);
    expect(audio.currentTime).toBe(0);
    vm.startAudio();
    expect(audio.play).toHaveBeenCalledTimes(1);
  });
  it('works without Media Session support', () => {
    delete navigator.mediaSession;
    const vm = mountPlayer();
    vm.startAudio();
    audio.emit('playing');
    expect(vm.isPlaying).toBe(true);
  });
  it('releases media and OS controls when leaving the office', () => {
    const vm = mountPlayer();
    wrapper.unmount();
    wrapper = null;
    expect(audio.pause).toHaveBeenCalled();
    expect(audio.removeAttribute).toHaveBeenCalledWith('src');
    expect(actions.play).toBe(null);
    expect(mediaSession.playbackState).toBe('none');
    audio.emit('playing');
    expect(vm.isPlaying).toBe(false);
  });
});

describe('AudioPlayer compact controls', () => {
  const initialWidth = window.innerWidth;
  beforeEach(() => {
    Object.defineProperty(window, 'innerWidth', {
      configurable: true,
      value: 375,
    });
  });
  afterEach(() => {
    Object.defineProperty(window, 'innerWidth', {
      configurable: true,
      value: initialWidth,
    });
  });

  it('plays and pauses from the compact bar', async () => {
    const vm = mountPlayer();
    await wrapper.get('[aria-label="Play audio"]').trigger('click');
    expect(audio.play).toHaveBeenCalledOnce();
    audio.paused = false;
    audio.emit('play');
    await vm.$nextTick();
    await wrapper.get('[aria-label="Pause audio"]').trigger('click');
    expect(audio.pause).toHaveBeenCalledOnce();
  });

  it('can dismiss paused audio from the bar or the options popover', async () => {
    const vm = mountPlayer();
    await vm.$nextTick();
    await wrapper.get('[aria-label="Hide audio controls"]').trigger('click');
    await wrapper.get('.preferences-button').trigger('click');
    await wrapper.get('.hide-player-button').trigger('click');
    expect(wrapper.emitted('dismiss-audio')).toHaveLength(2);
    audio.paused = false;
    audio.emit('play');
    await vm.$nextTick();
    expect(wrapper.find('[aria-label="Hide audio controls"]').exists()).toBe(
      false
    );
    expect(wrapper.find('.hide-player-button').exists()).toBe(false);
  });

  it('exposes loading instead of an enabled play button before audio is ready', async () => {
    mountPlayer();
    await wrapper.setProps({ audioReady: false });
    expect(
      wrapper.get('[aria-label="Play audio"]').attributes('disabled')
    ).toBeDefined();
    expect(wrapper.text()).toContain('Preparing audio');
  });

  it('jumps to a section from the current-section menu', async () => {
    const vm = mountPlayer();
    await vm.$nextTick();
    const trigger = wrapper.get('.section-button');
    expect(trigger.text()).toContain('Reading');
    expect(trigger.attributes('aria-expanded')).toBe('false');
    await trigger.trigger('click');
    expect(trigger.attributes('aria-expanded')).toBe('true');
    const item = wrapper.get('.section-item');
    expect(item.text()).toContain('Reading');
    expect(item.text()).toContain('1:00');
    await item.trigger('click');
    expect(audio.play).toHaveBeenCalledOnce();
    expect(audio.currentTime).toBe(59);
    expect(trigger.attributes('aria-expanded')).toBe('false');
  });

  it('opens listening options without moving controls and closes with Escape', async () => {
    const vm = mountPlayer();
    await vm.$nextTick();
    const options = wrapper.get('.preferences-button');
    expect(options.attributes('aria-expanded')).toBe('false');
    expect(wrapper.get('.preferences-panel').isVisible()).toBe(false);
    await options.trigger('click');
    expect(options.attributes('aria-expanded')).toBe('true');
    await wrapper
      .get('.highlight-control input[value="sentence"]')
      .setValue(true);
    await wrapper.get('.scroll-control').trigger('click');
    expect(vm.highlightMode).toBe('sentence');
    expect(vm.enableScrolling).toBe(false);
    expect(DynamicStorage.setItem).toHaveBeenCalledWith(
      'audioAutoScroll',
      'false'
    );
    await wrapper.get('.scroll-control').trigger('keydown', { key: 'Escape' });
    expect(options.attributes('aria-expanded')).toBe('false');
    expect(wrapper.get('.preferences-panel').isVisible()).toBe(false);
    await options.trigger('click');
    expect(wrapper.get('.highlight-control input:checked').element.value).toBe(
      'sentence'
    );
  });

  it('closes an open popover when the other one opens or on outside press', async () => {
    const vm = mountPlayer();
    await vm.$nextTick();
    await wrapper.get('.section-button').trigger('click');
    await wrapper.get('.preferences-button').trigger('click');
    expect(vm.showSections).toBe(false);
    expect(vm.showPreferences).toBe(true);
    document.body.dispatchEvent(
      new window.Event('pointerdown', { bubbles: true })
    );
    expect(vm.showPreferences).toBe(false);
  });

  it('applies and remembers speed changes and 15-second skips', async () => {
    const vm = mountPlayer();
    await vm.$nextTick();
    await wrapper.get('.preferences-button').trigger('click');
    for (let step = 0; step < 5; step += 1) {
      await wrapper.get('[aria-label="Faster"]').trigger('click');
    }
    expect(audio.playbackRate).toBe(1.5);
    expect(audio.defaultPlaybackRate).toBe(1.5);
    expect(wrapper.get('.speed-badge').text()).toBe('1.5×');
    expect(DynamicStorage.setItem).toHaveBeenLastCalledWith(
      'audioPlaybackSpeed',
      '1.5x'
    );
    await wrapper.get('[aria-label="Slower"]').trigger('click');
    expect(audio.playbackRate).toBe(1.4);
    await wrapper.get('[aria-label="Forward 15 seconds"]').trigger('click');
    expect(audio.currentTime).toBe(15);
    await wrapper.get('[aria-label="Back 15 seconds"]').trigger('click');
    expect(audio.currentTime).toBe(0);
  });

  it('restores saved speed and auto-scroll preferences', async () => {
    DynamicStorage.getItem.mockImplementation(
      async (key) =>
        ({ audioPlaybackSpeed: '1.2x', audioAutoScroll: 'false' })[key]
    );
    const vm = mountPlayer();
    await Promise.resolve();
    await vm.$nextTick();
    expect(vm.playbackSpeed).toBe('1.2x');
    expect(audio.playbackRate).toBe(1.2);
    expect(vm.enableScrolling).toBe(false);
  });

  it('reports layout changes and disconnects its resize observer', async () => {
    const observe = vi.fn();
    const disconnect = vi.fn();
    let onResize;
    vi.stubGlobal(
      'ResizeObserver',
      class {
        constructor(callback) {
          onResize = callback;
        }
        observe = observe;
        disconnect = disconnect;
      }
    );
    const event = vi.fn();
    document.addEventListener('audio-player-visibility', event);
    const vm = mountPlayer();
    await vm.$nextTick();
    expect(observe).toHaveBeenCalledOnce();
    onResize();
    expect(event.mock.lastCall[0].detail.visible).toBe(true);
    wrapper.unmount();
    wrapper = null;
    expect(disconnect).toHaveBeenCalledOnce();
    expect(event.mock.lastCall[0].detail.visible).toBe(false);
    document.removeEventListener('audio-player-visibility', event);
  });
});
