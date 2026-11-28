// @vitest-environment jsdom

import { mount } from '@vue/test-utils';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import ChantText from '@/components/ChantText.vue';
import {
  buildTimeline,
  createChantPlayer,
  createRecordingPlayer,
  recordingUrl,
  syllableAt,
  transposeFor,
  verseStart,
} from '@/helpers/chantPlayer';

// "The Lord is my shepherd; * therefore" in Tone VIII, cut short.
const FIRST = [
  { t: 'The', r: 'intonation', p: [55], d: [1] },
  { t: ' ', r: '' },
  { t: 'Lord', r: 'intonation', p: [57], d: [1] },
  { t: ' is my ', r: '' },
  { t: '', r: 'bar' },
  { t: 'shep', r: 'accent', p: [62], d: [1] },
  { t: 'herd', r: 'final', p: [60], d: [2] },
  { t: ';', r: '' },
];
const SECOND = [{ t: 'there', r: '', p: [60, 59], d: [1, 1] }];

describe('buildTimeline', () => {
  it('gives each syllable its pulses and rests at the asterisk and between verses', () => {
    const verses = [
      { number: 1, halves: [FIRST, SECOND] },
      { number: 2, halves: [[], SECOND] },
    ];
    const timeline = buildTimeline(verses, { pulse: 1, transpose: -3 });
    expect(timeline.syllables.map((s) => [s.verse, s.half, s.index])).toEqual([
      [1, 0, 0],
      [1, 0, 2],
      [1, 0, 5],
      [1, 0, 6],
      [1, 1, 0],
      [2, 1, 0],
    ]);
    // 1 + 1 + 1 + 2 pulses, a rest of 3 at the asterisk.
    expect(timeline.syllables[4].start).toBe(8);
    // "there" has two notes; one pulse between verses; verse 2 has an empty
    // first half that still rests at the asterisk.
    expect(timeline.syllables[4].end).toBe(10);
    expect(timeline.syllables[5].start).toBe(14);
    expect(timeline.notes[0]).toEqual({ midi: 52, start: 0, end: 1 });
    expect(timeline.duration).toBe(16);
  });

  it('takes fractional lengths and breathes after a comma', () => {
    const half = [
      { t: 'Lord', r: '', p: [60], d: [0.75], w: 0.5 },
      { t: ', ', r: '' },
      { t: 'my', r: '', p: [60], d: [0.75] },
    ];
    const timeline = buildTimeline([{ number: 1, halves: [half, []] }], { pulse: 1 });
    expect(timeline.syllables[0].end).toBe(0.75);
    // Half a pulse of breath before "my".
    expect(timeline.syllables[1].start).toBe(1.25);
    expect(syllableAt(timeline, 1)).toBeNull();
  });

  it('finds where a whole-psalm recording reaches a verse', () => {
    const verses = [
      { number: 1, halves: [FIRST, SECOND] },
      { number: 2, halves: [[], SECOND] },
    ];
    const timeline = buildTimeline(verses, { pulse: 1 });
    expect(verseStart(timeline, null)).toBe(0);
    expect(verseStart(timeline, 2)).toBe(14);
    expect(verseStart(timeline, 9)).toBe(0);
  });

  it('resolves a recording path against the API', () => {
    expect(recordingUrl('/uploads/chant/psalm-23.mp3', 'https://api.example.com/')).toBe(
      'https://api.example.com/uploads/chant/psalm-23.mp3'
    );
    expect(recordingUrl(null)).toBeNull();
  });

  it('finds the syllable sounding at a time', () => {
    const timeline = buildTimeline([{ number: 1, halves: [FIRST, SECOND] }], {
      pulse: 1,
    });
    expect(syllableAt(timeline, 3.5).index).toBe(6);
    expect(syllableAt(timeline, 5.5)).toBeNull(); // the rest at the asterisk
    expect(syllableAt(timeline, 8.2).half).toBe(1);
  });

  it('puts the reciting note at the chosen pitch', () => {
    expect(transposeFor('medium', 60)).toBe(-3);
    expect(transposeFor('high', 65)).toBe(-3);
    expect(transposeFor('nonsense', 57)).toBe(0);
  });
});

class FakeParam {
  setValueAtTime() {}
  linearRampToValueAtTime() {}
}

class FakeContext {
  constructor() {
    this.currentTime = 0;
    this.state = 'running';
    this.started = [];
    FakeContext.last = this;
  }
  node() {
    return { connect() {}, gain: new FakeParam(), frequency: { value: 0 } };
  }
  createPeriodicWave() {
    return {};
  }
  createBiquadFilter() {
    return this.node();
  }
  createGain() {
    return this.node();
  }
  createOscillator() {
    const oscillator = {
      ...this.node(),
      setPeriodicWave() {},
      start: (at) => this.started.push(at),
      stop: vi.fn(),
    };
    return oscillator;
  }
  get destination() {
    return {};
  }
}

describe('createChantPlayer', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    window.AudioContext = FakeContext;
  });
  afterEach(() => {
    vi.useRealTimers();
    delete window.AudioContext;
  });

  it('schedules notes, reports syllables, and stops at the end', async () => {
    const positions = [];
    const onEnd = vi.fn();
    const player = createChantPlayer({
      onPosition: (s) => positions.push(s && s.index),
      onEnd,
    });
    const timeline = buildTimeline([{ number: 1, halves: [FIRST, []] }], {
      pulse: 0.5,
    });
    expect(await player.play(timeline)).toBe(true);
    expect(player.playing).toBe(true);
    // Everything within the lookahead is scheduled at once.
    expect(FakeContext.last.started.length).toBe(3);
    FakeContext.last.currentTime = 0.1 + 1.1;
    vi.advanceTimersByTime(60);
    expect(positions).toContain(5);
    FakeContext.last.currentTime = 10;
    vi.advanceTimersByTime(60);
    expect(player.playing).toBe(false);
    expect(onEnd).toHaveBeenCalledTimes(1);
    expect(positions.at(-1)).toBeNull();
  });

  it('says so when the device has no Web Audio', async () => {
    delete window.AudioContext;
    const onEnd = vi.fn();
    const player = createChantPlayer({ onEnd });
    const timeline = buildTimeline([{ number: 1, halves: [FIRST, []] }]);
    expect(await player.play(timeline)).toBe(false);
    expect(onEnd).toHaveBeenCalled();
  });
});

class FakeAudio {
  static last = null;
  static refuse = false;
  constructor(src) {
    this.src = src;
    this.dataset = {};
    this.readyState = 4;
    this.currentTime = 0;
    this.play = vi.fn(() =>
      FakeAudio.refuse
        ? Promise.reject(new Error('NotSupportedError'))
        : Promise.resolve()
    );
    this.pause = vi.fn();
    FakeAudio.last = this;
  }
  addEventListener() {}
}

describe('createRecordingPlayer', () => {
  const URL_ = 'https://api.example.org/uploads/chant/psalm-23.mp3';
  const timeline = buildTimeline([{ number: 1, halves: [FIRST, SECOND] }]);
  let originalAudio;
  beforeEach(() => {
    vi.useFakeTimers();
    originalAudio = window.Audio;
    window.Audio = FakeAudio;
    globalThis.Audio = FakeAudio;
    window.URL.createObjectURL = vi.fn(() => 'blob:recording');
    window.URL.revokeObjectURL = vi.fn();
  });
  afterEach(() => {
    vi.useRealTimers();
    window.Audio = originalAudio;
    globalThis.Audio = originalAudio;
    delete window.fetch;
  });

  it('plays the recording from memory when it can be fetched', async () => {
    window.fetch = vi.fn(() =>
      Promise.resolve({ ok: true, blob: () => Promise.resolve(new Blob()) })
    );
    const player = createRecordingPlayer();
    expect(await player.play(URL_, timeline)).toBe(true);
    expect(FakeAudio.last.src).toBe('blob:recording');
    expect(FakeAudio.last.play).toHaveBeenCalled();
    player.stop();
  });

  it('plays straight from the address when the fetch is refused', async () => {
    // What a browser does when the server sends no CORS header.
    window.fetch = vi.fn(() => Promise.reject(new TypeError('Failed to fetch')));
    const player = createRecordingPlayer();
    expect(await player.play(URL_, timeline)).toBe(true);
    expect(FakeAudio.last.src).toBe(URL_);
    expect(FakeAudio.last.play).toHaveBeenCalled();
    player.stop();
  });

  it('says so when the recording cannot be played at all', async () => {
    window.fetch = vi.fn(() => Promise.resolve({ ok: false, status: 404 }));
    FakeAudio.refuse = true;
    const onEnd = vi.fn();
    const player = createRecordingPlayer({ onEnd });
    expect(await player.play(URL_, timeline)).toBe(false);
    expect(FakeAudio.last.src).toBe(URL_);
    expect(player.playing).toBe(false);
    FakeAudio.refuse = false;
  });
});

describe('ChantText highlighting', () => {
  it('highlights the syllable being sung', () => {
    const wrapper = mount(ChantText, { props: { segments: FIRST, active: 5 } });
    expect(wrapper.find('.is-sung').text()).toBe('shep');
  });

  it('keeps the marks on responses without pitches', () => {
    const old = FIRST.map(({ t, r }) => ({ t, r }));
    const wrapper = mount(ChantText, { props: { segments: old } });
    expect(wrapper.find('.chant-accent').text()).toBe('shep');
  });
});

describe('ChantPlayer', () => {
  it('asks for a reload when the psalm has marks but no notes', async () => {
    const { default: ChantPlayer } =
      await import('@/components/ChantPlayer.vue');
    const { default: UiKit } = await import('@/ui');
    const old = FIRST.map(({ t, r }) => ({ t, r }));
    const wrapper = mount(ChantPlayer, {
      props: {
        verses: [{ number: 1, chant: { first_half: old, second_half: [] } }],
        tone: { tenor: 60, demo: null },
      },
      global: { plugins: [UiKit] },
    });
    expect(wrapper.text()).toContain('Reload the page');
    expect(wrapper.text()).not.toContain('Play the psalm');

    await wrapper.setProps({
      verses: [{ number: 1, chant: { first_half: FIRST, second_half: [] } }],
    });
    expect(wrapper.text()).toContain('Play the psalm');
  });
});
