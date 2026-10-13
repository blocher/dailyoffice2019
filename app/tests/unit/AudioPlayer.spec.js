// @vitest-environment jsdom

import { mount } from '@vue/test-utils';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import AudioPlayer from '@/components/AudioPlayer.vue';
import { DynamicStorage } from '@/helpers/storage';

vi.mock('@/helpers/storage', () => ({
  DynamicStorage: { getItem: vi.fn(), setItem: vi.fn() },
}));

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

const setHighlight = (wrapper, mode) =>
  wrapper.get(`.highlight-control input[value="${mode}"]`).setValue(true);

const mountPlayer = (source = audio) =>
  mount(AudioPlayer, {
    attachTo: document.body,
    data: () => ({ showPreferences: true }),
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
      },
    },
  });

describe('AudioPlayer word synchronization', () => {
  let content;

  beforeEach(() => {
    DynamicStorage.getItem.mockResolvedValue(null);
    DynamicStorage.setItem.mockResolvedValue();
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
    expect(globalThis.cancelAnimationFrame).toHaveBeenCalled();
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

  it.each([null, '', 'invalid'])(
    'defaults to word mode for stored %s',
    async (stored) => {
      DynamicStorage.getItem.mockResolvedValue(stored);
      const wrapper = mountPlayer();
      await wrapper.vm.$nextTick();
      expect(wrapper.vm.highlightMode).toBe('word');
      expect(
        wrapper.get('.highlight-control input:checked').element.value
      ).toBe('word');
      wrapper.unmount();
    }
  );

  it.each(['word', 'sentence', 'off'])(
    'restores saved %s mode',
    async (mode) => {
      DynamicStorage.getItem.mockResolvedValue(mode);
      const wrapper = mountPlayer();
      await wrapper.vm.$nextTick();
      wrapper.vm.updateActiveWord(0.5);
      expect(wrapper.vm.highlightMode).toBe(mode);
      expect(Boolean(content.querySelector('.audio-line--active'))).toBe(
        mode !== 'off'
      );
      wrapper.unmount();
    }
  );

  it('offers an accessible native control and persists its selection', async () => {
    const wrapper = mountPlayer();
    await wrapper.vm.$nextTick();
    const group = wrapper.get('fieldset.highlight-control');
    expect(group.get('legend').text()).toContain('Highlight');
    expect(group.findAll('label').map((label) => label.text())).toEqual([
      'Word',
      'Sentence',
      'Off',
    ]);
    await setHighlight(wrapper, 'sentence');
    expect(DynamicStorage.setItem).toHaveBeenCalledWith(
      'audioHighlightMode',
      'sentence'
    );
    expect(wrapper.vm.enableScrolling).toBe(true);
    wrapper.unmount();
  });

  it.each([
    'The <em>Lord</em> speaks. We give thanks.',
    'The <em>Lord speaks with mercy and kindness to all who seek him in prayer and thanksgiving every morning. We give</em> thanks for the blessings of this day and ask for guidance as we go about our work in peace.',
  ])('groups measured sentences across inline markup: %s', async (markup) => {
    content.innerHTML = `<span data-line-id="line-one"></span><p>${markup}</p>`;
    const source = [...audio];
    source[4] = [
      {
        id: 'line-one',
        word: 'The',
        start_time: 0,
        end_time: 0.3,
        provider: 'elevenlabs',
      },
      {
        id: 'line-one',
        word: 'Lord',
        start_time: 0.4,
        end_time: 1,
        provider: 'elevenlabs',
      },
      {
        id: 'line-one',
        word: 'We',
        start_time: 2,
        end_time: 3,
        provider: 'elevenlabs',
      },
    ];
    const original = content.querySelector('p').textContent;
    const emphasis = content.querySelector('em').textContent;
    const wrapper = mountPlayer(source);
    await wrapper.vm.$nextTick();
    await setHighlight(wrapper, 'sentence');
    const highlighted = () =>
      Array.from(content.querySelectorAll('.audio-line--active'))
        .map((element) => element.textContent)
        .join('');
    wrapper.vm.updateActiveWord(0.5);
    expect(highlighted()).toBe(original.slice(0, original.indexOf('We')));
    wrapper.vm.updateActiveWord(2.5);
    expect(highlighted()).toBe(original.slice(original.indexOf('We')));
    wrapper.vm.updateActiveWord(0.5);
    expect(highlighted()).toBe(original.slice(0, original.indexOf('We')));
    expect(content.querySelector('em').textContent).toBe(emphasis);
    expect(content.querySelectorAll('[aria-current="true"]')).toHaveLength(1);
    wrapper.unmount();
  });

  it('keeps toggles idempotent and Off clear through seeks and clock updates', async () => {
    const source = [...audio];
    source[4] = audio[4].map((word) => ({ ...word, provider: 'elevenlabs' }));
    const wrapper = mountPlayer(source);
    await wrapper.vm.$nextTick();
    wrapper.vm.enableScrolling = false;
    wrapper.vm.audioElement.currentTime = 0.5;
    await setHighlight(wrapper, 'sentence');
    const wrappers = content.querySelectorAll('span').length;
    for (let iteration = 0; iteration < 5; iteration += 1) {
      for (const mode of ['word', 'sentence', 'off']) {
        await setHighlight(wrapper, mode);
        expect(wrapper.vm.audioElement.currentTime).toBe(0.5);
        if (mode === 'off') {
          for (const time of [0.15, 0.5, 0.8]) {
            wrapper.vm.seekTo(time);
            wrapper.vm.handleTimeUpdate();
            wrapper.vm.updateActiveWord(time);
            expect(content.querySelector('.audio-line--active')).toBeNull();
            expect(content.querySelector('[aria-current]')).toBeNull();
          }
          wrapper.vm.audioElement.currentTime = 0.5;
        }
      }
    }
    expect(content.querySelectorAll('span')).toHaveLength(wrappers);
    expect(content.querySelector('p').textContent).toBe('The Lord speaks.');
    expect(wrapper.vm.audioElement.play).not.toHaveBeenCalled();
    expect(wrapper.vm.enableScrolling).toBe(false);
    wrapper.unmount();
  });

  it('keeps independent word following enabled while highlights are Off', async () => {
    const wrapper = mountPlayer();
    await wrapper.vm.$nextTick();
    await setHighlight(wrapper, 'off');
    wrapper.vm.isPlaying = true;
    const word = content.querySelector('.audio-word');
    word.getBoundingClientRect = () => ({ top: 900, bottom: 930 });
    word.scrollIntoView = vi.fn();
    wrapper.vm.updateActiveWord(0.15);
    expect(word.scrollIntoView).toHaveBeenCalledTimes(1);
    expect(content.querySelector('.audio-line--active')).toBeNull();
    wrapper.unmount();
  });

  it('uses estimated clip bounds for sentences without measured timing', async () => {
    content.innerHTML =
      '<span data-line-id="line-one"></span><p>The <em>Lord speaks.</em> We give thanks.</p>';
    const source = [...audio];
    source[3] = [{ id: 'line-one', start_time: 1, end_time: 5 }];
    source[4] = [];
    const wrapper = mountPlayer(source);
    await wrapper.vm.$nextTick();
    await setHighlight(wrapper, 'sentence');
    expect(wrapper.vm.highlightSegments).toHaveLength(2);
    expect(
      wrapper.vm.highlightSegments.every((segment) => segment.estimated)
    ).toBe(true);
    wrapper.vm.updateActiveWord(1.5);
    expect(
      Array.from(content.querySelectorAll('.audio-line--active'))
        .map((element) => element.textContent)
        .join('')
    ).toBe('The Lord speaks. ');
    wrapper.vm.updateActiveWord(4);
    expect(content.querySelector('.audio-line--active').textContent).toBe(
      'We give thanks.'
    );
    wrapper.vm.updateActiveWord(6);
    expect(content.querySelector('.audio-line--active')).toBeNull();
    wrapper.unmount();
  });

  it('keeps every mode safe when timing and section data are absent', async () => {
    const source = ['/audio/unknown.mp3', '', [], [], []];
    const wrapper = mountPlayer(source);
    await wrapper.vm.$nextTick();
    expect(wrapper.find('.highlight-control input').exists()).toBe(true);
    for (const mode of ['sentence', 'off', 'word']) {
      await setHighlight(wrapper, mode);
      wrapper.vm.updateActiveWord(2);
      expect(wrapper.vm.highlightSegments).toHaveLength(0);
      expect(content.querySelector('.audio-line--active')).toBeNull();
      expect(content.querySelector('[aria-current]')).toBeNull();
    }
    wrapper.unmount();
  });

  it('does not let a late storage read override a user choice or unmount', async () => {
    let resolve;
    DynamicStorage.getItem.mockReturnValue(
      new Promise((done) => {
        resolve = done;
      })
    );
    const wrapper = mountPlayer();
    await wrapper.vm.$nextTick();
    await setHighlight(wrapper, 'off');
    resolve('sentence');
    await wrapper.vm.$nextTick();
    expect(wrapper.vm.highlightMode).toBe('off');
    wrapper.unmount();
    DynamicStorage.getItem.mockReturnValue(
      new Promise((done) => {
        resolve = done;
      })
    );
    const removed = mountPlayer();
    removed.unmount();
    resolve('sentence');
    await Promise.resolve();
    expect(content.querySelector('.audio-line--active')).toBeNull();
  });

  it('works when saving the preference fails', async () => {
    DynamicStorage.setItem.mockRejectedValue(new Error('unavailable'));
    const wrapper = mountPlayer();
    await wrapper.vm.$nextTick();
    await setHighlight(wrapper, 'off');
    await Promise.resolve();
    expect(wrapper.vm.highlightMode).toBe('off');
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
  it.each(['word', 'sentence'])('disables estimated highlights only for unavailable chunks in %s mode', async (mode) => {
    content.innerHTML = "<span data-line-id='line-one'></span><p>The Lord speaks.</p><span data-line-id='line-two'></span><p>We respond.</p>";
    const source = [...audio];
    source[3] = [
      { id: 'line-one', start_time: 0, end_time: 5, highlighting_available: false },
      { id: 'line-two', start_time: 5, end_time: 12 },
    ];
    source[4] = [];
    const wrapper = mountPlayer(source);
    await wrapper.vm.$nextTick();
    await setHighlight(wrapper, mode);
    expect(wrapper.vm.highlightSegments.length).toBeGreaterThan(0);
    expect(wrapper.vm.highlightSegments.every((segment) => segment.start_time >= 5)).toBe(true);
    expect(wrapper.vm.activeWordAt(1)).toBe(-1);
    expect(wrapper.vm.activeWordAt(6)).toBeGreaterThanOrEqual(0);
    wrapper.vm.updateActiveWord(6);
    expect(content.querySelector('.audio-line--active')).not.toBeNull();
    wrapper.vm.updateActiveWord(1);
    expect(content.querySelector('.audio-line--active')).toBeNull();
    wrapper.unmount();
  });

  it('suppresses measured highlights in explicitly unavailable audio while playback remains usable', async () => {
    const source = [...audio];
    source[3] = [{ id: 'line-one', start_time: 0, end_time: 5, highlighting_available: false }];
    source[4] = audio[4].map((word) => ({ ...word, provider: 'elevenlabs' }));
    const wrapper = mountPlayer(source);
    await wrapper.vm.$nextTick();
    wrapper.vm.updateActiveWord(0.4);
    expect(content.querySelector('.audio-line--active')).toBeNull();
    await wrapper.vm.audioElement.play();
    expect(wrapper.vm.audioElement.play).toHaveBeenCalled();
    wrapper.unmount();
  });

});
