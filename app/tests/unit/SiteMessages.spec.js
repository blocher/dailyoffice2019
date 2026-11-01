import { afterEach, describe, expect, it, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';

const platform = vi.hoisted(() => ({ name: 'web' }));
vi.mock('@capacitor/core', () => ({
  Capacitor: {
    getPlatform: () => platform.name,
    isNativePlatform: () => platform.name !== 'web',
  },
}));
vi.mock('@capacitor/browser', () => ({ Browser: { open: vi.fn() } }));
vi.mock('@capacitor/app', () => ({
  App: { getInfo: vi.fn(async () => ({ version: '4.1.0', build: '7' })) },
}));

import SiteMessages from '@/components/SiteMessages.vue';
import { panels } from '@/helpers/panels';
import {
  dismissAllWhatsNew,
  dismissWhatsNew,
  earlierWhatsNew,
  newWhatsNew,
  summarizeTitles,
  whatsNewState,
} from '@/helpers/whatsNew';

const message = {
  uuid: 'abc',
  title: 'Hello',
  body: 'World',
  dismiss_permanent: true,
};

function mountComponent() {
  return mount(SiteMessages, {
    global: {
      mocks: { $http: { get: vi.fn(async () => ({ data: [message] })) } },
      stubs: { UiIcon: true, UiButton: true, UiTag: true },
    },
  });
}

afterEach(() => {
  platform.name = 'web';
  vi.restoreAllMocks();
  window.localStorage.clear();
  window.sessionStorage.clear();
  whatsNewState.entries = [];
  whatsNewState.dismissed = [];
  panels.whatsNew = false;
});

describe('SiteMessages request', () => {
  function requestParams() {
    const get = vi.fn(async () => ({ data: [] }));
    mount(SiteMessages, {
      global: {
        mocks: { $http: { get } },
        stubs: { UiIcon: true, UiTag: true },
      },
    });
    return flushPromises().then(() => get.mock.calls[0][1].params);
  }

  it('sends only the platform from the web', async () => {
    expect(await requestParams()).toEqual({
      platform: 'web',
      kinds: 'notice,whats_new',
    });
  });

  it('sends the store version from the native apps', async () => {
    platform.name = 'ios';
    expect(await requestParams()).toEqual({
      platform: 'ios',
      kinds: 'notice,whats_new',
      app_version: '4.1.0',
    });
  });
});

describe('SiteMessages with blocked storage', () => {
  it('still shows messages when reading storage throws a SecurityError', async () => {
    const denied = () => {
      throw new DOMException('Access is denied', 'SecurityError');
    };
    vi.spyOn(window, 'localStorage', 'get').mockImplementation(denied);
    vi.spyOn(window, 'sessionStorage', 'get').mockImplementation(denied);
    const wrapper = mountComponent();
    await flushPromises();
    expect(wrapper.vm.visibleMessages).toHaveLength(1);
    expect(() => wrapper.vm.dismiss(message)).not.toThrow();
    expect(wrapper.vm.visibleMessages).toHaveLength(0);
  });
});

describe('SiteMessages links', () => {
  it('follows the link from the tag as well as the text', async () => {
    const push = vi.fn();
    const wrapper = mount(SiteMessages, {
      global: {
        mocks: {
          $http: {
            get: vi.fn(async () => ({
              data: [{ ...message, tag_text: 'Book View!', link: '?book=1' }],
            })),
          },
          $router: { push },
        },
        stubs: { UiIcon: true, UiButton: true, RouterLink: true },
      },
    });
    await flushPromises();
    await wrapper.find('.site-message__tag').trigger('click');
    expect(push).toHaveBeenCalledWith('?book=1');
  });

  it('leaves a tag without a link inert', async () => {
    const push = vi.fn();
    const wrapper = mount(SiteMessages, {
      global: {
        mocks: {
          $http: {
            get: vi.fn(async () => ({
              data: [{ ...message, tag_text: 'New', link: '' }],
            })),
          },
          $router: { push },
        },
        stubs: { UiIcon: true, UiButton: true },
      },
    });
    await flushPromises();
    const tag = wrapper.find('.site-message__tag');
    expect(tag.classes()).not.toContain('is-link');
    await tag.trigger('click');
    expect(push).not.toHaveBeenCalled();
  });
});

const entry = (uuid, title) => ({
  uuid,
  kind: 'whats_new',
  title,
  text: `${title} is here.`,
  link: '',
  dismissible: true,
  dismiss_permanent: true,
});

function mountWith(data) {
  return mount(SiteMessages, {
    global: {
      mocks: { $http: { get: vi.fn(async () => ({ data })) } },
      stubs: { UiIcon: true, UiTag: true },
    },
  });
}

describe("What's New entries", () => {
  const banner = (wrapper) => wrapper.find('.whats-new-banner');

  it('share one banner, with a count, instead of a banner each', async () => {
    const wrapper = mountWith([
      { ...message, uuid: 'notice', text: 'A notice' },
      entry('a', 'Offline mode'),
      entry('b', 'Book view'),
      entry('c', 'Podcasts'),
    ]);
    await flushPromises();
    expect(wrapper.findAll('.site-message')).toHaveLength(1);
    expect(banner(wrapper).find('.whats-new-banner__count').text()).toBe('3');
    expect(banner(wrapper).text()).toContain(
      'Offline mode, Book view, and 1 more'
    );
  });

  it('open the sheet from the banner without dismissing anything', async () => {
    const wrapper = mountWith([entry('a', 'Offline mode')]);
    await flushPromises();
    await banner(wrapper).find('.whats-new-banner__open').trigger('click');
    expect(panels.whatsNew).toBe(true);
    expect(newWhatsNew.value).toHaveLength(1);
    expect(banner(wrapper).exists()).toBe(true);
  });

  it('are all dismissed by the banner’s close button, for good', async () => {
    const wrapper = mountWith([
      entry('a', 'Offline mode'),
      entry('b', 'Book view'),
    ]);
    await flushPromises();
    await banner(wrapper).find('.whats-new-banner__close').trigger('click');
    expect(banner(wrapper).exists()).toBe(false);
    expect(
      JSON.parse(window.localStorage.getItem('dismissedWhatsNew'))
    ).toEqual(['a', 'b']);
  });

  it('can be dismissed one at a time', async () => {
    const wrapper = mountWith([
      entry('a', 'Offline mode'),
      entry('b', 'Book view'),
    ]);
    await flushPromises();
    dismissWhatsNew({ uuid: 'a' });
    await flushPromises();
    expect(banner(wrapper).find('.whats-new-banner__count').text()).toBe('1');
    expect(banner(wrapper).text()).toContain('Book view');
    expect(banner(wrapper).text()).not.toContain('Offline mode');
    expect(earlierWhatsNew.value.map((e) => e.uuid)).toEqual(['a']);
  });

  it('count as dismissed when their old banner was dismissed', async () => {
    window.localStorage.setItem('dismissedSiteMessages', JSON.stringify(['a']));
    const wrapper = mountWith([
      entry('a', 'Book view'),
      entry('b', 'Offline mode'),
    ]);
    await flushPromises();
    expect(newWhatsNew.value.map((e) => e.uuid)).toEqual(['b']);
    expect(banner(wrapper).text()).not.toContain('Book view');
  });

  it('bring the banner back only for an entry added later', async () => {
    mountWith([entry('a', 'Offline mode')]);
    await flushPromises();
    dismissAllWhatsNew();
    const wrapper = mountWith([
      entry('a', 'Offline mode'),
      entry('b', 'Widgets'),
    ]);
    await flushPromises();
    expect(banner(wrapper).text()).toContain('Widgets');
    expect(banner(wrapper).text()).not.toContain('Offline');
  });

  it('come as notices from a server that predates them', async () => {
    const { kind, ...old } = entry('a', 'Offline mode');
    expect(kind).toBe('whats_new');
    const wrapper = mountWith([old]);
    await flushPromises();
    expect(banner(wrapper).exists()).toBe(false);
    expect(wrapper.findAll('.site-message')).toHaveLength(1);
  });
});

describe('summarizeTitles', () => {
  it('names one, two, or the first two and a count', () => {
    const e = (title) => ({ title });
    expect(summarizeTitles([e('A')])).toBe('A');
    expect(summarizeTitles([e('A'), e('B')])).toBe('A and B');
    expect(summarizeTitles([e('A'), e('B'), e('C'), e('D')])).toBe(
      'A, B, and 2 more'
    );
  });
});
