// @vitest-environment jsdom

import { mount } from '@vue/test-utils';
import { beforeEach, describe, expect, it } from 'vitest';

import ChantText from '@/components/ChantText.vue';
import OfficeCongregation from '@/components/OfficeCongregation.vue';
import OfficeLeader from '@/components/OfficeLeader.vue';
import { displayState } from '@/helpers/displayPreferences';

// "The Lord is my shepherd;" pointed to Tone VIII (first verse).
const SEGMENTS = [
  { t: 'The', r: 'intonation' },
  { t: ' ', r: '' },
  { t: 'Lord', r: 'intonation' },
  { t: ' is my ', r: '' },
  { t: '', r: 'bar' },
  { t: 'shep', r: 'accent' },
  { t: 'herd', r: 'final' },
  { t: ';', r: '' },
];

describe('ChantText', () => {
  it('keeps the words and marks the inflection', () => {
    const wrapper = mount(ChantText, { props: { segments: SEGMENTS } });
    expect(wrapper.text().replace('|', '')).toBe('The Lord is my shepherd;');
    expect(wrapper.find('.chant-bar').attributes('aria-hidden')).toBe('true');
    expect(wrapper.find('.chant-accent').text()).toBe('shep');
    expect(wrapper.findAll('.chant-prep').map((w) => w.text())).toEqual([
      'The',
      'Lord',
    ]);
  });
});

describe('office psalm lines', () => {
  const line = {
    content: 'The Lord is my shepherd; *',
    preface: 1,
    indented: 'hangingIndent',
    chant: SEGMENTS,
  };

  beforeEach(() => {
    displayState.chantMode = false;
  });

  it('show plain text unless chant mode is on', async () => {
    for (const component of [OfficeLeader, OfficeCongregation]) {
      displayState.chantMode = false;
      const wrapper = mount(component, { props: { line } });
      expect(wrapper.find('.chant-text').exists()).toBe(false);
      displayState.chantMode = true;
      await wrapper.vm.$nextTick();
      expect(wrapper.find('.chant-accent').text()).toBe('shep');
      expect(wrapper.text()).toContain('*');
    }
  });

  it('ignore chant mode for lines that are not pointed', () => {
    displayState.chantMode = true;
    const wrapper = mount(OfficeLeader, {
      props: {
        line: { content: 'O Lord, open our lips;', line_type: 'leader' },
      },
    });
    expect(wrapper.find('.chant-text').exists()).toBe(false);
    expect(wrapper.text()).toContain('O Lord, open our lips;');
  });
});
