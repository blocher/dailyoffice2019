import { flushPromises, mount, RouterLinkStub } from '@vue/test-utils';
import { afterEach, describe, expect, it, vi } from 'vitest';
import Podcasts from '../../src/views/Podcasts.vue';
import UiKit from '../../src/ui';
import { isWithinAudioWindow } from '../../src/helpers/officeAudio';

const { getMock, getItemMock, setItemMock, writeMock, settings } = vi.hoisted(
  () => ({
    getMock: vi.fn(),
    getItemMock: vi.fn(),
    setItemMock: vi.fn().mockResolvedValue(),
    writeMock: vi.fn().mockResolvedValue(),
    settings: { language_style: 'contemporary' },
  })
);

vi.mock('axios', () => ({ default: { get: getMock } }));
vi.mock('vuex', () => ({ useStore: () => ({ state: { settings } }) }));
vi.mock('@capacitor/clipboard', () => ({ Clipboard: { write: writeMock } }));
vi.mock('@/helpers/storage', () => ({
  DynamicStorage: { getItem: getItemMock, setItem: setItemMock },
}));

function feed(slug, group, style, extra = {}) {
  return {
    slug,
    title: slug,
    subtitle: `${slug} subtitle`,
    group,
    style,
    is_readings: group === 'readings',
    feed_url: `https://api.example/podcasts/${slug}.xml`,
    artwork_small_url: `https://api.example/podcasts/artwork/${slug}-600.jpg`,
    listings: [],
    latest_episode: null,
    ...extra,
  };
}

const CATALOG = {
  groups: [
    { slug: 'daily-office', title: 'The Daily Office', description: '' },
    { slug: 'readings', title: 'Just the Readings', description: '' },
  ],
  feeds: [
    feed('morning-prayer', 'daily-office', 'contemporary', {
      latest_episode: {
        title: 'Tuesday, October 13, 2026: Edward the Confessor',
        duration: 1500,
        audio_url: 'https://api.example/podcasts/episodes/x.mp3',
        follow_along_url:
          'https://www.dailyoffice2019.com/morning_prayer/2026/10/13?psalter=60',
      },
      listings: [
        {
          platform: 'apple',
          label: 'Apple Podcasts',
          url: 'https://podcasts.apple.com/x',
        },
      ],
    }),
    feed('morning-prayer-traditional', 'daily-office', 'traditional'),
    feed('daily-office-readings', 'readings', 'contemporary'),
    feed('daily-office-readings-traditional', 'readings', 'traditional'),
  ],
  live_alternative: {
    title: 'The Daily Office Podcast',
    host: 'Andrew Russell',
    description: 'Recorded daily.',
    links: [{ platform: 'spotify', url: 'https://example.com/spotify' }],
  },
};

async function mountPage() {
  getMock.mockResolvedValue({ data: CATALOG });
  const wrapper = mount(Podcasts, {
    attachTo: document.body,
    global: {
      plugins: [UiKit],
      stubs: { RouterLink: RouterLinkStub },
    },
  });
  await flushPromises();
  return wrapper;
}

function cardTitles(wrapper) {
  return wrapper.findAll('.podcast-card__title').map((node) => node.text());
}

describe('Podcasts landing page', () => {
  afterEach(() => {
    document.body.innerHTML = '';
    vi.clearAllMocks();
    settings.language_style = 'contemporary';
  });

  it('lists the offices and readings in the chosen language', async () => {
    getItemMock.mockResolvedValue(null);
    const wrapper = await mountPage();
    expect(getMock).toHaveBeenCalledWith(
      expect.stringMatching(/api\/v1\/podcasts$/)
    );
    expect(cardTitles(wrapper)).toEqual([
      'morning-prayer',
      'daily-office-readings',
    ]);
    await wrapper
      .findAll('button')
      .find((button) => button.text() === 'Traditional language')
      .trigger('click');
    expect(cardTitles(wrapper)).toEqual([
      'morning-prayer-traditional',
      'daily-office-readings-traditional',
    ]);
    expect(setItemMock).toHaveBeenCalledWith('podcastStyle', 'traditional');
    wrapper.unmount();
  });

  it('starts in traditional language for readers who pray that way', async () => {
    getItemMock.mockResolvedValue(null);
    settings.language_style = 'traditional';
    const wrapper = await mountPage();
    expect(cardTitles(wrapper)[0]).toBe('morning-prayer-traditional');
    wrapper.unmount();
  });

  it('offers the human-voice podcast before our own', async () => {
    getItemMock.mockResolvedValue('contemporary');
    const wrapper = await mountPage();
    const aside = wrapper.find('.podcast-alternative');
    const ours = wrapper.find('.podcasts-ours');
    expect(aside.text()).toContain('Prefer a human voice?');
    expect(aside.text()).toContain('The Daily Office Podcast.');
    expect(aside.find('a').attributes('href')).toBe(
      'https://example.com/spotify'
    );
    expect(
      aside.element.compareDocumentPosition(ours.element) &
        Node.DOCUMENT_POSITION_FOLLOWING
    ).toBeTruthy();
    expect(ours.find('.podcast-card').exists()).toBe(true);
    wrapper.unmount();
  });

  it('links the latest episode to the office inside the app', async () => {
    getItemMock.mockResolvedValue('contemporary');
    const wrapper = await mountPage();
    const link = wrapper.findComponent(RouterLinkStub);
    expect(link.props('to')).toBe('/morning_prayer/2026/10/13?psalter=60');
    expect(wrapper.text()).toContain('(25 min)');
    wrapper.unmount();
  });

  it('offers directory, app, and RSS subscriptions', async () => {
    getItemMock.mockResolvedValue('contemporary');
    const wrapper = await mountPage();
    await wrapper
      .findAll('button')
      .find((button) => button.text() === 'Subscribe')
      .trigger('click');
    await flushPromises();
    const hrefs = [...document.body.querySelectorAll('.subscribe__link')].map(
      (link) => link.getAttribute('href')
    );
    // The Apple Podcasts listing replaces the generic podcast:// link.
    expect(hrefs).toContain('https://podcasts.apple.com/x');
    expect(hrefs).not.toContain(
      'podcast://api.example/podcasts/morning-prayer.xml'
    );
    expect(hrefs).toContain(
      'overcast://x-callback-url/add?url=https%3A%2F%2Fapi.example%2Fpodcasts%2Fmorning-prayer.xml'
    );
    expect(hrefs).toContain(
      'pktc://subscribe/api.example/podcasts/morning-prayer.xml'
    );
    const input = document.body.querySelector('.subscribe__feed input');
    expect(input.value).toBe('https://api.example/podcasts/morning-prayer.xml');
    const copy = [
      ...document.body.querySelectorAll('.subscribe__feed button'),
    ][0];
    copy.click();
    await flushPromises();
    expect(writeMock).toHaveBeenCalledWith({
      string: 'https://api.example/podcasts/morning-prayer.xml',
    });
    wrapper.unmount();
  });

  it('shows an error with a retry when the catalog cannot load', async () => {
    getItemMock.mockResolvedValue(null);
    getMock.mockRejectedValueOnce(new Error('offline'));
    const wrapper = mount(Podcasts, {
      global: { plugins: [UiKit], stubs: { RouterLink: RouterLinkStub } },
    });
    await flushPromises();
    expect(wrapper.text()).toContain('couldn’t be loaded');
    wrapper.unmount();
  });
});

describe('audio date window', () => {
  it('runs from three days ago through nine days ahead', () => {
    const today = new Date(2026, 9, 13, 12);
    expect(isWithinAudioWindow(new Date(2026, 9, 10), today)).toBe(true);
    expect(isWithinAudioWindow(new Date(2026, 9, 22, 23, 0), today)).toBe(true);
    expect(isWithinAudioWindow(new Date(2026, 9, 9, 23, 0), today)).toBe(false);
    expect(isWithinAudioWindow(new Date(2026, 9, 23), today)).toBe(false);
  });
});
