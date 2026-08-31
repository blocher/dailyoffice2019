// @vitest-environment jsdom

import { mount } from '@vue/test-utils';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import AudioPlayer from '@/components/AudioPlayer.vue';

class MockAudio extends window.EventTarget {
  constructor(source) {
    super();
    this.src = source;
    this.currentTime = 0;
    this.duration = 12;
    this.readyState = 4;
    this.HAVE_ENOUGH_DATA = 4;
    this.playbackRate = 1;
    this.seekable = { length: 1, end: () => this.duration };
    this.play = vi.fn().mockResolvedValue();
    this.pause = vi.fn();
  }

  load() {}
}

const audio = [
  '/audio/full.mp3',
  '/uploads/full.mp3',
  [
    { name: 'Opening', start_time: 0 },
    { name: 'Psalm', start_time: 5 },
  ],
  [{ id: 'line-one', start_time: 0 }],
  [
    {
      id: 'line-one',
      word: 'The',
      start_time: 0.1,
      end_time: 0.3,
    },
    {
      id: 'line-one',
      word: 'Lord',
      start_time: 0.35,
      end_time: 0.65,
    },
    {
      id: 'line-one',
      word: 'speaks',
      start_time: 0.7,
      end_time: 1,
    },
  ],
];

const mountPlayer = () =>
  mount(AudioPlayer, {
    attachTo: document.body,
    props: {
      audio,
      audioReady: true,
      office: 'morning_prayer',
      isEsvOrKjv: true,
      isWithinSevenDays: true,
    },
    global: {
      stubs: {
        Loading: true,
        'el-select': { template: '<div><slot /></div>' },
        'el-option': { template: '<span><slot /></span>' },
        'font-awesome-icon': true,
      },
    },
  });

describe('AudioPlayer word synchronization', () => {
  let content;

  beforeEach(() => {
    vi.stubGlobal('Audio', MockAudio);
    Object.defineProperty(window, 'innerWidth', {
      configurable: true,
      value: 1024,
    });
    content = document.createElement('main');
    content.innerHTML =
      "<span data-line-id='line-one'></span><p>The Lord speaks.</p>";
    document.body.appendChild(content);
  });

  afterEach(() => {
    document.body.innerHTML = '';
    vi.unstubAllGlobals();
  });

  it('wraps rendered words and precisely activates the currently spoken word', async () => {
    const wrapper = mountPlayer();
    await wrapper.vm.$nextTick();

    const words = content.querySelectorAll('.audio-word');
    expect(words).toHaveLength(3);

    wrapper.vm.audioElement.currentTime = 0.15;
    wrapper.vm.handleTimeUpdate();
    expect(words[0].classList.contains('audio-word--active')).toBe(true);

    wrapper.vm.audioElement.currentTime = 0.5;
    wrapper.vm.handleTimeUpdate();
    expect(words[0].classList.contains('audio-word--active')).toBe(false);
    expect(words[1].classList.contains('audio-word--active')).toBe(true);

    wrapper.unmount();
  });

  it('auto-scrolls when the active word leaves the readable viewport', async () => {
    const wrapper = mountPlayer();
    await wrapper.vm.$nextTick();
    wrapper.vm.isPlaying = true;

    const word = content.querySelector('[data-audio-word-index="0"]');
    word.getBoundingClientRect = () => ({
      top: 900,
      bottom: 930,
    });
    word.scrollIntoView = vi.fn();

    wrapper.vm.updateActiveWord(0.15);

    expect(word.scrollIntoView).toHaveBeenCalledWith({
      behavior: 'smooth',
      block: 'center',
    });
    wrapper.unmount();
  });

  it('supports transport seeking and reports the current module', async () => {
    const wrapper = mountPlayer();
    await wrapper.vm.$nextTick();

    wrapper.vm.audioElement.currentTime = 6;
    wrapper.vm.currentTime = 6;
    await wrapper.vm.$nextTick();
    expect(wrapper.vm.currentSectionName).toBe('Psalm');

    wrapper.vm.skipBy(15);
    expect(wrapper.vm.audioElement.currentTime).toBe(12);
    wrapper.vm.skipBy(-15);
    expect(wrapper.vm.audioElement.currentTime).toBe(0);
    wrapper.unmount();
  });
});
