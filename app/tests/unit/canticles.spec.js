import { flushPromises, mount, RouterLinkStub } from '@vue/test-utils';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createStore } from 'vuex';
import UiKit from '../../src/ui';
import LIBRARY from './canticles.fixture.json';

const { getMock, routeState, replaceMock } = vi.hoisted(() => ({
  getMock: vi.fn(),
  routeState: { name: 'Canticles', query: {}, params: {} },
  replaceMock: vi.fn(),
}));

vi.mock('axios', () => ({ default: { get: getMock } }));
vi.mock('@/helpers/storage', () => ({
  DynamicStorage: {
    getItem: vi.fn().mockResolvedValue(null),
    setItem: vi.fn().mockResolvedValue(),
  },
}));
vi.mock('vue-router', () => ({
  useRoute: () => routeState,
  useRouter: () => ({
    replace: (to) => {
      replaceMock(to);
      routeState.query = to.query || {};
      return Promise.resolve();
    },
  }),
}));

import {
  buildAppointments,
  describeAppointments,
  filterCanticles,
  resetCanticleLibrary,
  searchCanticle,
} from '../../src/helpers/canticles';
import Canticles from '../../src/views/Canticles.vue';

const appointments = buildAppointments(LIBRARY);
const noFilters = { search: '', office: '', rotation: '', season: '', day: '' };
const slugs = (filters) =>
  filterCanticles(LIBRARY, appointments, { ...noFilters, ...filters }).map(
    (r) => r.canticle.slug
  );

describe('canticle filters', () => {
  it('lists everything with no filters', () => {
    expect(slugs({})).toHaveLength(LIBRARY.canticles.length);
  });

  it('answers "what is said on a Tuesday morning in Lent" for a rotation', () => {
    expect(
      slugs({
        rotation: '1979',
        office: 'morning',
        day: 'tuesday',
        season: 'lent',
      })
    ).toEqual(['venite', 'jubilate', 'benedictus-es-domine', 'dignus-es']);
  });

  it('keeps the Pascha Nostrum to Eastertide', () => {
    expect(slugs({ season: 'easter', office: 'morning' })).toContain(
      'pascha-nostrum'
    );
    expect(slugs({ season: 'advent', office: 'morning' })).not.toContain(
      'pascha-nostrum'
    );
  });

  it('filters by office, including Compline', () => {
    expect(slugs({ office: 'compline' })).toEqual(['nunc-dimittis']);
    expect(slugs({ office: 'evening', rotation: 'default' })).toEqual([
      'phos-hilaron',
      'magnificat',
      'nunc-dimittis',
    ]);
  });

  it('includes the date-specific exceptions of the seasonal rotation', () => {
    expect(slugs({ rotation: '2011', office: 'evening' })).toContain(
      'cantate-domino'
    );
  });
});

describe('canticle search', () => {
  const benedictus = LIBRARY.canticles.find((c) => c.slug === 'benedictus');

  it('matches names and citations', () => {
    expect(searchCanticle(benedictus, 'zechariah')).toEqual({ where: 'title' });
    expect(searchCanticle(benedictus, 'luke 1:68')).toEqual({ where: 'title' });
  });

  it('matches a line of the text in either style, ignoring quotes and case', () => {
    const contemporary = benedictus.texts.contemporary[0].content;
    const words = contemporary.split(' ').slice(1, 4).join(' ').toUpperCase();
    expect(searchCanticle(benedictus, words)).toMatchObject({
      where: 'text',
      line: contemporary,
      style: 'contemporary',
    });
    const traditional = benedictus.texts.traditional[0].content;
    expect(
      searchCanticle(benedictus, traditional.slice(0, 20), 'traditional')
    ).toMatchObject({ where: 'text', style: 'traditional' });
  });

  it('returns null when nothing matches', () => {
    expect(searchCanticle(benedictus, 'xylophone')).toBeNull();
  });
});

describe('appointment summaries', () => {
  it('describes where a canticle falls in a rotation', () => {
    const lines = describeAppointments(
      LIBRARY,
      appointments['ecce-deus'],
      '1979'
    );
    expect(lines).toEqual([
      { label: 'Morning Prayer, first canticle', when: ['Monday'] },
      { label: 'Evening Prayer, first canticle', when: ['Saturday'] },
    ]);
  });

  it('says "every day" when a canticle fills every row', () => {
    const [line] = describeAppointments(
      LIBRARY,
      appointments['magnificat'],
      '2011'
    );
    expect(line.when).toEqual(['Every day']);
  });

  it('names seasons when a canticle is seasonal', () => {
    const [line] = describeAppointments(
      LIBRARY,
      appointments['benedictus-es-domine'],
      'default'
    );
    expect(line.when).toEqual(['Every day in Lent & Holy Week']);
  });
});

describe('Canticles page', () => {
  beforeEach(() => {
    resetCanticleLibrary();
    getMock.mockResolvedValue({ data: LIBRARY });
    routeState.query = {};
    replaceMock.mockClear();
  });

  async function mountPage(settings = {}) {
    const store = createStore({ state: { settings } });
    const wrapper = mount(Canticles, {
      global: {
        plugins: [UiKit, store],
        stubs: { RouterLink: RouterLinkStub, Ornament: true },
      },
    });
    await flushPromises();
    return wrapper;
  }

  it('lists every canticle, grouped as the book groups them', async () => {
    const wrapper = await mountPage();
    expect(getMock).toHaveBeenCalledWith(
      expect.stringContaining('api/v1/canticles')
    );
    expect(wrapper.findAll('.canticle-entry')).toHaveLength(
      LIBRARY.canticles.length
    );
    expect(
      wrapper.findAll('.canticle-group__title').map((h) => h.text())
    ).toEqual([
      'Invitatories',
      'The Evening Hymn',
      'Morning Canticles',
      'Evening Canticles',
      'Supplemental Canticles',
      'Other Canticles',
    ]);
  });

  it('reads its filters from the URL and marks text matches', async () => {
    routeState.query = { q: 'zechariah' };
    let wrapper = await mountPage();
    expect(wrapper.findAll('.canticle-entry')).toHaveLength(1);

    resetCanticleLibrary();
    // A line of the Te Deum that is not also its title.
    const line = LIBRARY.canticles.find((c) => c.slug === 'te-deum').texts
      .contemporary[1].content;
    routeState.query = { q: line.slice(4, 20) };
    wrapper = await mountPage();
    expect(wrapper.find('.canticle-entry__snippet mark').text()).toBe(
      line.slice(4, 20)
    );
  });

  it('shows the rotation table for the user’s own setting', async () => {
    routeState.query = { view: 'rotations' };
    const wrapper = await mountPage({ canticle_rotation: '2011' });
    expect(wrapper.text()).toContain('Your setting');
    const days = wrapper.findAll('.rotation-row__day').map((d) => d.text());
    expect(days[0]).toContain('Sunday');
    expect(days[1]).toContain('Monday – Friday');
  });
});
