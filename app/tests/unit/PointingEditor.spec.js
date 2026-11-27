// @vitest-environment jsdom

import { flushPromises, mount } from '@vue/test-utils';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import PointingEditor from '@/components/PointingEditor.vue';
import UiKit from '@/ui';

const { getMock, postMock } = vi.hoisted(() => ({
  getMock: vi.fn(),
  postMock: vi.fn(),
}));
vi.mock('axios', () => ({ default: { get: getMock, post: postMock } }));

// Psalm 23:1 as the API gives it, pointed from the St. Bernard Psalter.
const EDITOR = {
  psalm: 23,
  verse: 1,
  tone: {
    code: 'B4.4',
    label: 'Tone IV.4 (St. Bernard Psalter)',
    book: true,
    tenor: 57,
  },
  tones: [
    { code: 'B4.4', label: 'Tone IV.4 (St. Bernard Psalter)', book: true },
    { code: '8.G', label: 'Tone VIII.G', book: false },
  ],
  status: 'book',
  source: 'book',
  first_half: [
    { t: 'The', m: '', w: true },
    { t: 'Lord', m: '', w: true },
    { t: 'is', m: '^', w: true },
    { t: 'my', m: '', w: true },
    { t: 'shep', m: '^', w: true },
    { t: 'herd;', m: '', w: false },
  ],
  second_half: [
    { t: 'there', m: '', w: true },
    { t: 'fore', m: '', w: false },
    { t: 'I', m: '^', w: true },
    { t: 'can', m: '', w: true },
    { t: 'lack', m: '', w: true },
    { t: 'no', m: '^', w: true },
    { t: 'thing.', m: '', w: false },
  ],
};

async function mountEditor() {
  const wrapper = mount(PointingEditor, {
    attachTo: document.body,
    props: { open: true, psalm: 23, verses: [1, 2], verse: 1 },
    global: { plugins: [UiKit] },
  });
  await flushPromises();
  return wrapper;
}

function syllable(text) {
  return [...document.querySelectorAll('.pointing-editor__syllable')].find(
    (button) => button.textContent.trim() === text
  );
}

describe('PointingEditor', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    getMock.mockResolvedValue({ data: EDITOR });
    postMock.mockResolvedValue({
      data: { first_half: [], second_half: [], warnings: [], tone: 'B4.4' },
    });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
    document.body.innerHTML = '';
  });

  it('loads the verse and shows the book’s marks', async () => {
    const wrapper = await mountEditor();
    expect(getMock).toHaveBeenCalledWith(
      expect.stringContaining('api/v1/psalms/23/verses/1/pointing')
    );
    expect(syllable('shep').classList).toContain('is-pointed');
    expect(syllable('lack').classList).not.toContain('is-pointed');
    wrapper.unmount();
  });

  it('cycles a syllable through bold, italic and plain, and previews it', async () => {
    const wrapper = await mountEditor();
    syllable('lack').click();
    await flushPromises();
    expect(syllable('lack').classList).toContain('is-pointed');
    expect(syllable('lack').classList).toContain('is-changed');
    syllable('lack').click();
    await flushPromises();
    expect(syllable('lack').classList).toContain('is-slur');

    vi.advanceTimersByTime(300);
    await flushPromises();
    const [url, body] = postMock.mock.calls.at(-1);
    expect(url).toContain('api/v1/pointing/preview');
    expect(body).toEqual({
      psalm: 23,
      verse: 1,
      first_half: 'The Lord ^is my ^shep/herd;',
      second_half: 'there/fore ^I can ~lack ^no/thing.',
      tone: 'B4.4',
    });

    syllable('lack').click();
    await flushPromises();
    expect(syllable('lack').classList).not.toContain('is-changed');
    wrapper.unmount();
  });

  it('sends a suggestion with its note and thanks the sender', async () => {
    const wrapper = await mountEditor();
    syllable('lack').click();
    await flushPromises();
    const send = [...document.querySelectorAll('button')].find((b) =>
      b.textContent.includes('Send suggestion')
    );
    send.click();
    await flushPromises();
    const [url, body] = postMock.mock.calls.find(([u]) =>
      u.includes('proposals')
    );
    expect(url).toContain('api/v1/pointing/proposals');
    expect(body.second_half).toBe('there/fore ^I can ^lack ^no/thing.');
    expect(document.body.textContent).toContain(
      'An editor will look at your suggestion'
    );
    wrapper.unmount();
  });
});
