import { beforeEach, describe, expect, it, vi } from 'vitest';
import { shallowMount } from '@vue/test-utils';

const share = vi.hoisted(() => ({
  canShare: vi.fn(async () => ({ value: true })),
  share: vi.fn(),
}));
const toast = vi.hoisted(() => ({ success: vi.fn(), error: vi.fn() }));

vi.mock('@capacitor/share', () => ({ Share: share }));
vi.mock('@capacitor/clipboard', () => ({ Clipboard: { write: vi.fn() } }));
vi.mock('@capacitor/core', () => ({
  Capacitor: { getPlatform: () => 'ios' },
}));
vi.mock('@/helpers/storage', () => ({
  DynamicStorage: { getItem: vi.fn(async () => null) },
}));
vi.mock('@/ui/feedback', () => ({ toast }));

import ShareSettings from '@/components/ShareSettings.vue';

function mountPanel() {
  return shallowMount(ShareSettings, {
    global: {
      mocks: {
        $route: { path: '/settings' },
        $store: {
          dispatch: vi.fn(),
          state: { settings: { psalter: '60' }, settingAbbreviations: [] },
        },
      },
    },
  });
}

describe('ShareSettings share()', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('stays quiet when the share sheet is dismissed', async () => {
    const wrapper = mountPanel();
    // What the native plugin rejects with on iOS and Android.
    share.share.mockRejectedValueOnce(new Error('Share canceled'));
    await expect(wrapper.vm.share()).resolves.toBeUndefined();
    // What navigator.share() rejects with on the web.
    share.share.mockRejectedValueOnce(
      Object.assign(new Error('The request is not allowed'), {
        name: 'AbortError',
      })
    );
    await expect(wrapper.vm.share()).resolves.toBeUndefined();
    expect(toast.error).not.toHaveBeenCalled();
  });

  it('points to the copy button when sharing really fails', async () => {
    const wrapper = mountPanel();
    share.share.mockRejectedValueOnce(new Error('Share API not available'));
    await expect(wrapper.vm.share()).resolves.toBeUndefined();
    expect(toast.error).toHaveBeenCalledTimes(1);
  });
});
