import { afterEach, describe, expect, it, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';

vi.mock('@capacitor/core', () => ({
  Capacitor: { getPlatform: () => 'web' },
}));
vi.mock('@capacitor/browser', () => ({ Browser: { open: vi.fn() } }));

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

afterEach(() => vi.restoreAllMocks());

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
