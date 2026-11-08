// @vitest-environment jsdom

import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';

import ChantScore from '@/components/ChantScore.vue';
import { parseGabcNotes } from '@/helpers/chantScore';

// Tone VIII.G as the API sends it.
const SCORE = {
  clef: 'c4',
  first_half: [
    { n: 'g', role: 'intonation' },
    { n: 'h', role: 'intonation' },
    { n: 'j', role: 'tenor' },
    { n: 'k', role: 'accent' },
    { n: 'j', role: 'return' },
    { n: 'j.', role: 'note' },
  ],
  second_half: [
    { n: 'j', role: 'tenor' },
    { n: 'i', role: 'note' },
    { n: 'j', role: 'note' },
    { n: 'h', role: 'accent' },
    { n: 'g', role: 'return' },
    { n: 'g.', role: 'note' },
  ],
};

describe('parseGabcNotes', () => {
  it('reads positions, flats, diamonds and dots', () => {
    expect(parseGabcNotes('ixi').flats).toEqual([8]);
    expect(parseGabcNotes('ixi').notes).toEqual([
      { position: 8, inclinatum: false, dots: 0 },
    ]);
    const climacus = parseGabcNotes('gvFED.').notes;
    expect(climacus.map((n) => n.inclinatum)).toEqual([
      false,
      true,
      true,
      true,
    ]);
    expect(climacus.at(-1).dots).toBe(1);
    expect(parseGabcNotes('gf..').notes.map((n) => n.dots)).toEqual([1, 1]);
  });
});

describe('ChantScore', () => {
  it('draws the tone with the reciting note open and accents marked', () => {
    const wrapper = mount(ChantScore, {
      props: { score: SCORE, label: 'Tone VIII.G' },
    });
    expect(wrapper.findAll('.chant-score__breve')).toHaveLength(2);
    expect(wrapper.findAll('.chant-score__accent')).toHaveLength(2);
    expect(wrapper.findAll('.chant-score__group--return')).toHaveLength(2);
    expect(wrapper.text()).toContain('Tone VIII.G');
  });

  it('lights the group "Hear the tone" is playing, despite the repeated reciting note', () => {
    const lit = (active) =>
      mount(ChantScore, { props: { score: SCORE, active } })
        .findAll('.is-sung')
        .map((g) => g.classes().find((c) => c.includes('--')));
    // The demo sings intonation (0, 1), the tenor three times (2-4), then
    // the cadence (5-7).
    expect(lit({ half: 0, index: 3 })).toEqual(['chant-score__group--tenor']);
    expect(lit({ half: 0, index: 5 })).toEqual(['chant-score__group--accent']);
    expect(lit({ half: 1, index: 5 })).toEqual(['chant-score__group--accent']);
    expect(lit(null)).toEqual([]);
  });
});
