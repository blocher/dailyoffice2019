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
  removeAttribute() {}
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

const mountPlayer = (source = audio) =>
  mount(AudioPlayer, {
    attachTo: document.body,
    props: {
      audio: source,
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

  it('highlights short words between sparse media timeupdate events', async () => {
    let frame;
    vi.stubGlobal(
      'requestAnimationFrame',
      vi.fn((callback) => {
        frame = callback;
        return 1;
      })
    );
    vi.stubGlobal('cancelAnimationFrame', vi.fn());
    const source = [...audio];
    source[4] = audio[4].map((word, index) => ({
      ...word,
      provider: 'elevenlabs',
      start_time: index * 0.08,
      end_time: (index + 1) * 0.08,
    }));
    const wrapper = mountPlayer(source);
    await wrapper.vm.$nextTick();
    wrapper.vm.enableScrolling = false;
    wrapper.vm.handlePlay();
    expect(frame).toBeTypeOf('function');
    for (const [time, word] of [
      [0.03, 'The'],
      [0.11, 'Lord'],
      [0.19, 'speaks'],
    ]) {
      wrapper.vm.audioElement.currentTime = time;
      frame();
      expect(content.querySelector('.audio-line--active')?.textContent).toBe(
        word
      );
    }
    wrapper.vm.handlePause();
    expect(cancelAnimationFrame).toHaveBeenCalled();
    wrapper.unmount();
  });

  it('matches the printed small-cap divine name to spoken Lord', async () => {
    content.innerHTML =
      "<span data-line-id='line-one'></span><p>The Lᴏʀᴅ speaks.</p>";
    const source = [...audio];
    source[4] = audio[4].map((word) => ({ ...word, provider: 'elevenlabs' }));
    const wrapper = mountPlayer(source);
    await wrapper.vm.$nextTick();
    expect(content.querySelectorAll('.audio-word')).toHaveLength(3);
    wrapper.vm.updateActiveWord(0.4);
    expect(content.querySelector('.audio-line--active')?.textContent).toBe(
      'Lᴏʀᴅ'
    );
    wrapper.unmount();
  });

  it('holds a whole line through short timing gaps and clears during silence', async () => {
    content.innerHTML =
      "<span data-line-id='line-one'></span><p>The merciful Lord speaks.</p>";
    const wrapper = mountPlayer();
    await wrapper.vm.$nextTick();
    const line = content.querySelector('[data-audio-line-content]');
    expect(line.tagName).toBe('SPAN');
    expect(line.parentElement.tagName).toBe('P');
    for (const time of [0.15, 0.5, 1.8]) {
      wrapper.vm.updateActiveWord(time);
      expect(line.classList.contains('audio-line--active')).toBe(true);
      expect(line.textContent).toBe('The merciful Lord speaks.');
    }
    wrapper.vm.updateActiveWord(4);
    expect(line.classList.contains('audio-line--active')).toBe(false);
    wrapper.unmount();
  });

  it('traces individual ElevenLabs words using direct start and end times', async () => {
    content.innerHTML =
      '<span data-line-id="line-one"></span><p>The <em>Lord</em> speaks.</p>';
    const source = [...audio];
    source[4] = audio[4].map((word) => ({ ...word, provider: 'elevenlabs' }));
    const wrapper = mountPlayer(source);
    await wrapper.vm.$nextTick();
    const highlighted = () =>
      Array.from(content.querySelectorAll('.audio-line--active'))
        .map((e) => e.textContent)
        .join('');
    wrapper.vm.updateActiveWord(0.15);
    expect(highlighted()).toBe('The');
    wrapper.vm.updateActiveWord(0.5);
    expect(highlighted()).toBe('Lord');
    wrapper.vm.updateActiveWord(0.68);
    expect(highlighted()).toBe('');
    wrapper.vm.updateActiveWord(0.8);
    expect(highlighted()).toBe('speaks');
    wrapper.vm.updateActiveWord(1.1);
    expect(highlighted()).toBe('');
    wrapper.vm.updateActiveWord(0.2);
    expect(highlighted()).toBe('The');
    expect(content.querySelector('em').textContent).toBe('Lord');
    wrapper.unmount();
  });

  it('highlights complete sentences in long readings and preserves markup', async () => {
    const first =
      'The Lord speaks with mercy and kindness to all who seek him in prayer and thanksgiving every morning. ';
    const second =
      'We give thanks for the blessings of this day and ask for guidance as we go about our work in peace.';
    content.innerHTML = `<span data-line-id="line-one"></span><p>${first}<em>${second}</em></p>`;
    const source = [...audio];
    source[4] = [
      {
        id: 'line-one',
        speaker: 'reader',
        word: 'The',
        start_time: 0.1,
        end_time: 0.4,
      },
      {
        id: 'line-one',
        speaker: 'reader',
        word: 'We',
        start_time: 1.5,
        end_time: 2,
      },
    ];
    const wrapper = mountPlayer(source);
    await wrapper.vm.$nextTick();
    const highlighted = () =>
      Array.from(content.querySelectorAll('.audio-line--active'))
        .map((e) => e.textContent)
        .join('');
    wrapper.vm.updateActiveWord(0.5);
    expect(highlighted()).toBe(first);
    wrapper.vm.updateActiveWord(1.6);
    expect(highlighted()).toBe(second);
    expect(content.querySelector('em').textContent).toBe(second);
    wrapper.vm.updateActiveWord(0.2);
    expect(highlighted()).toBe(first);
    wrapper.unmount();
    expect(content.querySelector('.audio-line--active')).toBeNull();
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

  it('follows later words in the same sentence only outside the middle third', async () => {
    const wrapper = mountPlayer();
    await wrapper.vm.$nextTick();
    wrapper.vm.isPlaying = true;
    const words = content.querySelectorAll('.audio-word');
    words[0].getBoundingClientRect = () => ({ top: 350, bottom: 380 });
    words[0].scrollIntoView = vi.fn();
    words[1].getBoundingClientRect = () => ({ top: 900, bottom: 930 });
    words[1].scrollIntoView = vi.fn();
    wrapper.vm.updateActiveWord(0.15);
    expect(words[0].scrollIntoView).not.toHaveBeenCalled();
    wrapper.vm.updateActiveWord(0.5);
    expect(words[1].scrollIntoView).toHaveBeenCalledTimes(1);
    wrapper.vm.updateActiveWord(0.55);
    expect(words[1].scrollIntoView).toHaveBeenCalledTimes(1);
    expect(content.querySelector('.audio-line--active').textContent).toBe(
      'The Lord speaks.'
    );
    wrapper.vm.enableScrolling = false;
    wrapper.vm.lastFollowScrollAt = -Infinity;
    wrapper.vm.updateActiveWord(0.6);
    expect(words[1].scrollIntoView).toHaveBeenCalledTimes(1);
    wrapper.unmount();
  });

  it('uses clip timings for dialogue with no matching words, excluding the role label', async () => {
    content.innerHTML = `<span data-line-id="line-one"></span><div class="row"><div class="column left"><p>People</p></div><div class="column right"><p>And our mouth shall proclaim your praise.</p></div></div>`;
    const source = [...audio];
    source[3] = [{ id: 'line-one', start_time: 1, end_time: 5 }];
    source[4] = [];
    const wrapper = mountPlayer(source);
    await wrapper.vm.$nextTick();
    wrapper.vm.updateActiveWord(3);
    expect(content.querySelector('.audio-line--active')?.textContent).toBe(
      'And our mouth shall proclaim your praise.'
    );
    wrapper.vm.updateActiveWord(6);
    expect(content.querySelector('.audio-line--active')).toBeNull();
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
