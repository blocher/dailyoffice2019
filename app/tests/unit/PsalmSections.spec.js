import { flushPromises, mount, RouterLinkStub } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';
import Psalm from '../../src/views/Psalm.vue';
import OfficeSubheading from '../../src/components/OfficeSubheading.vue';
import UiKit from '../../src/ui';

const { getItemMock } = vi.hoisted(() => ({ getItemMock: vi.fn() }));

vi.mock('@/helpers/storage', () => ({
  DynamicStorage: {
    getItem: getItemMock,
    setItem: vi.fn().mockResolvedValue(),
  },
}));

function verse(number, sectionHeading = '') {
  return {
    id: number,
    number,
    section_heading: sectionHeading,
    first_half: `First half ${number}`,
    second_half: `Second half ${number}`,
    first_half_tle: `Traditional first half ${number}`,
    second_half_tle: `Traditional second half ${number}`,
    chant: null,
  };
}

const PSALM = {
  number: 119,
  latin_title: 'Beati immaculati',
  topics: [],
  chant_tone: { score: null, label: 'Tone VI', book: false },
  chant_recording: null,
  verses: [verse(8), verse(9, 'Beth'), verse(10)],
};

async function mountPsalm(traditional) {
  getItemMock.mockResolvedValue(traditional);
  const wrapper = mount(Psalm, {
    global: {
      plugins: [UiKit],
      stubs: {
        RouterLink: RouterLinkStub,
        ChantPlayer: true,
        ChantScore: true,
        PointingEditor: true,
        Ornament: true,
      },
      mocks: {
        $route: { params: { number: '119' } },
        $http: { get: vi.fn().mockResolvedValue({ data: PSALM }) },
      },
    },
  });
  await flushPromises();
  return wrapper;
}

describe('Psalm 119 sections', () => {
  it.each([false, true])(
    'heads a section with its letter, apart from the verse (traditional: %s)',
    async (traditional) => {
      const wrapper = await mountPsalm(traditional);
      const headings = wrapper.findAll('h4.psalm-section');
      expect(headings.map((h) => h.text())).toEqual(['Beth']);
      const text = wrapper.find('.psalm-text').text();
      // Above verse 9, after verse 8.
      expect(text.indexOf('Beth')).toBeGreaterThan(
        text.indexOf('econd half 8')
      );
      expect(text.indexOf('Beth')).toBeLessThan(text.indexOf('irst half 9'));
    }
  );

  it('sets an office psalm section line as a section heading', () => {
    const section = mount(OfficeSubheading, {
      props: { line: { content: 'Beth', psalm_section: true } },
    });
    expect(section.classes()).toContain('psalm-section');
    expect(section.text()).toBe('Beth');
    const plain = mount(OfficeSubheading, {
      props: { line: { content: 'Thirty Day Cycle' } },
    });
    expect(plain.classes()).not.toContain('psalm-section');
  });
});
