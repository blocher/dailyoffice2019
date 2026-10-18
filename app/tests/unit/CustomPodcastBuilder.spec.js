import { flushPromises, mount } from '@vue/test-utils';
import { afterEach, describe, expect, it, vi } from 'vitest';
import CustomPodcastBuilder from '../../src/components/CustomPodcastBuilder.vue';
import UiKit from '../../src/ui';
import {
  customizableSettings,
  podcastApps,
  snapshotSettings,
} from '../../src/helpers/podcasts';

const { postMock, writeMock, store } = vi.hoisted(() => ({
  postMock: vi.fn(),
  writeMock: vi.fn().mockResolvedValue(),
  store: {
    state: { settings: {}, availableSettings: [] },
    dispatch: vi.fn(),
    commit: vi.fn(),
  },
}));

vi.mock('axios', () => ({ default: { post: postMock } }));
vi.mock('vuex', () => ({ useStore: () => store }));
vi.mock('@capacitor/clipboard', () => ({ Clipboard: { write: writeMock } }));

const OFFICE_KEYS = [
  'bible_translation',
  'display_language',
  'family-creed',
  'language_style',
  'psalm_translation',
  'psalter',
];
const OPTIONS = {
  types: [
    {
      slug: 'daily-office',
      title: 'The Daily Office',
      description: 'The four offices.',
      offices: [
        {
          service: 'office/morning_prayer',
          title: 'Morning Prayer',
          is_readings: false,
        },
        { service: 'office/compline', title: 'Compline', is_readings: false },
      ],
    },
    {
      slug: 'family',
      title: 'Family Prayer',
      description: 'Short devotions.',
      offices: [
        {
          service: 'family/morning_prayer',
          title: 'Family Prayer in the Morning',
          is_readings: false,
        },
      ],
    },
    {
      slug: 'readings',
      title: 'Just the Readings',
      description: 'Scripture alone.',
      offices: [
        {
          service: 'readings/daily_office',
          title: 'Daily Office Readings',
          is_readings: true,
        },
        {
          service: 'readings/morning_prayer',
          title: 'Readings for Morning Prayer',
          is_readings: true,
        },
      ],
    },
  ],
  office_settings: {
    keys: OFFICE_KEYS,
    defaults: {
      bible_translation: 'esv',
      display_language: 'english',
      'family-creed': 'family-creed-yes',
      language_style: 'contemporary',
      psalm_translation: 'contemporary',
      psalter: '60',
    },
  },
  readings_settings: {
    keys: ['psalms', 'psalter', 'style', 'translation'],
    defaults: {
      translation: 'esv',
      psalms: 'contemporary',
      style: 'whole_verse',
      psalter: '60',
    },
    choices: {
      translation: ['esv', 'kjv'],
      psalms: ['contemporary', 'traditional'],
      style: ['whole_verse', 'half_verse', 'unison'],
      psalter: ['30', '60'],
    },
  },
  audio: {
    display_language: ['english'],
    language_style: ['contemporary', 'traditional'],
    bible_translation: ['esv', 'kjv'],
    psalm_translation: ['contemporary', 'traditional'],
  },
  window_days: 7,
  publish_hour: 2,
};

function setting(name, site, values, order) {
  return {
    uuid: name,
    name,
    title: name,
    site_name: site,
    setting_type: 1,
    order,
    options: values.map((value) => ({
      uuid: `${name}-${value}`,
      value,
      name: value,
    })),
  };
}

const AVAILABLE = [
  setting('bible_translation', 'Daily Office', ['esv', 'rsv', 'kjv'], 1),
  setting('display_language', 'Daily Office', ['english', 'spanish'], 2),
  setting('psalter', 'Daily Office', ['60', '30'], 3),
  setting(
    'language_style',
    'Daily Office',
    ['contemporary', 'traditional', 'spanish'],
    4
  ),
  setting(
    'psalm_translation',
    'Daily Office',
    ['contemporary', 'traditional', 'spanish'],
    5
  ),
  setting(
    'family-creed',
    'Family Prayer',
    ['family-creed-yes', 'family-creed-no'],
    1
  ),
  setting('theme', 'Daily Office', ['light', 'dark'], 9),
];

const FEED = {
  token: 'abc123XYZ_-',
  title: 'My Morning Prayer (Experimental) — The Daily Office',
  style_label: 'Contemporary language, English Standard Version (ESV)',
  feed_url: 'https://api.example/podcasts/custom/abc123XYZ_-.xml',
  artwork_url: 'https://api.example/podcasts/artwork/morning-prayer-600.jpg',
};

function mountBuilder() {
  return mount(CustomPodcastBuilder, {
    props: { options: OPTIONS },
    attachTo: document.body,
    global: { plugins: [UiKit], mocks: { $store: store } },
  });
}

async function choose(wrapper, name, value) {
  await wrapper
    .find(`input[name="custom-podcast-${name}"][value="${value}"]`)
    .trigger('change');
}

function button(wrapper, text) {
  return wrapper.findAll('button').find((node) => node.text().includes(text));
}

describe('custom podcast builder', () => {
  afterEach(() => {
    document.body.innerHTML = '';
    vi.clearAllMocks();
  });

  it('is labeled experimental and asks for feedback', () => {
    store.state.settings = {};
    const wrapper = mountBuilder();
    expect(wrapper.find('.ui-tag').text()).toBe('Experimental');
    const mail = wrapper.find('a[href^="mailto:"]');
    expect(mail.attributes('href')).toBe(
      'mailto:feedback@dailyoffice2019.com?subject=Custom%20podcast%20feedback'
    );
    wrapper.unmount();
  });

  it('lists the offices of the chosen type', async () => {
    store.state.settings = {};
    const wrapper = mountBuilder();
    expect(
      wrapper.findAll('.choice__title').map((node) => node.text())
    ).toEqual(['Daily Office', 'Family Prayer', 'Readings']);
    await choose(wrapper, 'type', 'readings');
    expect(
      wrapper.findAll('.choice__title').map((node) => node.text())
    ).toEqual(['Daily Office Readings', 'Readings for Morning Prayer']);
    wrapper.unmount();
  });

  it('makes a feed from a snapshot of my settings, read in the ESV', async () => {
    store.state.settings = {
      bible_translation: 'rsv',
      psalter: '30',
      language_style: 'traditional',
      theme: 'dark',
    };
    postMock.mockResolvedValue({ data: FEED });
    const wrapper = mountBuilder();
    await choose(wrapper, 'type', 'daily-office');
    await choose(wrapper, 'office', 'office/morning_prayer');
    expect(wrapper.text()).toContain('changes some of your settings to fit');
    await button(wrapper, 'Continue').trigger('click');
    await choose(wrapper, 'app', 'overcast');
    await button(wrapper, 'Make my podcast').trigger('click');
    await flushPromises();

    expect(postMock).toHaveBeenCalledTimes(1);
    const [url, body] = postMock.mock.calls[0];
    expect(url).toMatch(/api\/v1\/podcasts\/custom$/);
    expect(body.service).toBe('office/morning_prayer');
    expect(body.settings).toEqual({
      bible_translation: 'esv',
      display_language: 'english',
      'family-creed': 'family-creed-yes',
      language_style: 'traditional',
      psalm_translation: 'contemporary',
      psalter: '30',
    });
    expect(store.state.settings.bible_translation).toBe('rsv');

    expect(wrapper.find('#custom-podcast-feed-url').element.value).toBe(
      FEED.feed_url
    );
    const subscribe = wrapper.find('a.builder-add__open');
    expect(subscribe.text()).toContain('Subscribe in Overcast');
    expect(subscribe.attributes('href')).toBe(
      `overcast://x-callback-url/add?url=${encodeURIComponent(FEED.feed_url)}`
    );
    expect(wrapper.text()).toContain('Tap + at the top, then Add URL.');
    await button(wrapper, 'Copy').trigger('click');
    await flushPromises();
    expect(writeMock).toHaveBeenCalledWith({ string: FEED.feed_url });
    wrapper.unmount();
  });

  it('customizes a local copy and never touches my settings', async () => {
    store.state.settings = { bible_translation: 'kjv', psalter: '60' };
    store.state.availableSettings = AVAILABLE;
    postMock.mockResolvedValue({ data: FEED });
    const wrapper = mountBuilder();
    await choose(wrapper, 'type', 'daily-office');
    await choose(wrapper, 'office', 'office/compline');
    await choose(wrapper, 'settings', 'custom');
    await flushPromises();

    const sheet = document.body.querySelector('.ui-sheet');
    expect(sheet.textContent).toContain('Settings for Compline');
    const titles = [...sheet.querySelectorAll('.setting-row__title')].map(
      (node) => node.firstChild.textContent.trim()
    );
    expect(titles).toEqual(
      expect.arrayContaining([
        'bible_translation',
        'display_language',
        'psalter',
      ])
    );
    expect(titles).not.toContain('theme'); // not a key the server takes

    // Only the translations and language the audio is read in.
    const row = (name) =>
      [...sheet.querySelectorAll('.setting-row')].find((node) =>
        node.querySelector('.setting-row__title').textContent.includes(name)
      );
    row('bible_translation').querySelector('button').click();
    await flushPromises();
    const values = [
      ...row('bible_translation').querySelectorAll('.setting-option__input'),
    ].map((input) => input.value);
    expect(values).toEqual(['esv', 'kjv']);

    row('psalter').querySelector('button').click();
    await flushPromises();
    const thirty = row('psalter').querySelector('input[value="30"]');
    thirty.checked = true;
    thirty.dispatchEvent(new window.Event('change'));
    await flushPromises();

    expect(store.dispatch).not.toHaveBeenCalled();
    expect(store.commit).not.toHaveBeenCalled();
    expect(store.state.settings).toEqual({
      bible_translation: 'kjv',
      psalter: '60',
    });
    expect(AVAILABLE[2].active).toBeUndefined(); // the shared list is untouched

    [...sheet.querySelectorAll('button')]
      .find((node) => node.textContent.includes('Done'))
      .click();
    await flushPromises();
    expect(wrapper.text()).toContain('1 changed from yours');
    await button(wrapper, 'Continue').trigger('click');
    await choose(wrapper, 'app', 'copy');
    await button(wrapper, 'Make my podcast').trigger('click');
    await flushPromises();
    const { settings } = postMock.mock.calls[0][1];
    expect(settings.psalter).toBe('30');
    expect(settings.bible_translation).toBe('kjv');
    expect(wrapper.find('a.builder-add__open').exists()).toBe(false);
    expect(wrapper.text()).toContain('Add by URL');
    wrapper.unmount();
  });

  it('says when it is rate limited', async () => {
    store.state.settings = {};
    postMock.mockRejectedValue({ response: { status: 429 } });
    const wrapper = mountBuilder();
    await choose(wrapper, 'type', 'family');
    await choose(wrapper, 'office', 'family/morning_prayer');
    await button(wrapper, 'Continue').trigger('click');
    await choose(wrapper, 'app', 'apple');
    expect(wrapper.text()).toContain('Spotify and YouTube Music');
    await button(wrapper, 'Make my podcast').trigger('click');
    await flushPromises();
    expect(wrapper.text()).toContain('several podcasts in a short time');
    wrapper.unmount();
  });
});

describe('custom podcast helpers', () => {
  it('snapshots the readings choices from my settings', () => {
    expect(
      snapshotSettings(OPTIONS, true, {
        bible_translation: 'kjv',
        psalm_translation: 'traditional',
        psalm_style: 'unison',
        psalter: '30',
      })
    ).toEqual({
      settings: {
        psalms: 'traditional',
        psalter: '30',
        style: 'unison',
        translation: 'kjv',
      },
      adjusted: [],
    });
    const nrsv = snapshotSettings(OPTIONS, true, {
      bible_translation: 'nrsvce',
    });
    expect(nrsv.settings.translation).toBe('esv');
    expect(nrsv.adjusted).toEqual(['translation']);
  });

  it('keeps English only', () => {
    const { settings, adjusted } = snapshotSettings(OPTIONS, false, {
      display_language: 'spanish',
    });
    expect(settings.display_language).toBe('english');
    expect(adjusted).toEqual(['display_language']);
    const rows = customizableSettings(AVAILABLE, OPTIONS);
    const language = rows.find((row) => row.name === 'display_language');
    expect(language.options.map((option) => option.value)).toEqual(['english']);
  });

  it('keeps traditional or contemporary language and the Coverdale psalters', () => {
    const { settings, adjusted } = snapshotSettings(OPTIONS, false, {
      language_style: 'spanish',
      psalm_translation: 'spanish',
    });
    expect(settings.language_style).toBe('contemporary');
    expect(settings.psalm_translation).toBe('contemporary');
    expect(adjusted).toEqual(['language_style', 'psalm_translation']);
    const rows = customizableSettings(AVAILABLE, OPTIONS);
    for (const name of ['language_style', 'psalm_translation']) {
      const row = rows.find((candidate) => candidate.name === name);
      expect(row.options.map((option) => option.value)).toEqual([
        'contemporary',
        'traditional',
      ]);
    }
    const readings = snapshotSettings(OPTIONS, true, {
      psalm_translation: 'spanish',
    });
    expect(readings.settings.psalms).toBe('contemporary');
    expect(readings.adjusted).toEqual(['psalms']);
  });

  it('gives each app its subscribe link', () => {
    const url = 'https://api.example/podcasts/custom/abc.xml';
    const links = Object.fromEntries(
      podcastApps(url, { title: 'My Compline' }).map((app) => [
        app.id,
        app.href,
      ])
    );
    expect(links).toEqual({
      apple: 'podcast://api.example/podcasts/custom/abc.xml',
      overcast: `overcast://x-callback-url/add?url=${encodeURIComponent(url)}`,
      pocket_casts: 'pktc://subscribe/api.example/podcasts/custom/abc.xml',
      castro: 'castros://subscribe/api.example/podcasts/custom/abc.xml',
      antennapod: `https://antennapod.org/deeplink/subscribe?url=${encodeURIComponent(url)}&title=My%20Compline`,
      podcast_addict: 'podcastaddict://api.example/podcasts/custom/abc.xml',
    });
    for (const app of podcastApps(url)) {
      expect(app.steps.length).toBeGreaterThan(0);
    }
  });
});
