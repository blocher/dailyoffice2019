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
    expect(await requestParams()).toEqual({ platform: 'web' });
  });

  it('sends the store version from the native apps', async () => {
    platform.name = 'ios';
    expect(await requestParams()).toEqual({
      platform: 'ios',
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
