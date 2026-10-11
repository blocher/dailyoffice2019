// @vitest-environment jsdom

import { shallowMount } from '@vue/test-utils';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import DisplaySettingsModule from '@/components/DisplaySettingsModule.vue';
import { DynamicStorage } from '@/helpers/storage';

vi.mock('@/helpers/storage', () => ({
  DynamicStorage: { getItem: vi.fn(), setItem: vi.fn() },
}));

const flush = () => new Promise((resolve) => setTimeout(resolve));

const mountModule = (props = {}) =>
  shallowMount(DisplaySettingsModule, {
    props: { collapsible: false, ...props },
    global: { renderStubDefaultSlot: true },
  });

describe('DisplaySettingsModule audio controls', () => {
  beforeEach(() => {
    DynamicStorage.getItem.mockResolvedValue(null);
    DynamicStorage.setItem.mockResolvedValue();
  });

  it('turns the switch off when the parent hides audio from the player', async () => {
    const wrapper = mountModule({ audioEnabled: true });
    await flush();
    expect(wrapper.vm.audioEnabledLocal).toBe(true);
    await wrapper.setProps({ audioEnabled: false });
    expect(wrapper.vm.audioEnabledLocal).toBe(false);
    await flush();
    expect(wrapper.text()).toContain('Off');
    expect(DynamicStorage.setItem).toHaveBeenCalledWith(
      'audioEnabled',
      'false'
    );
  });

  it('hides the audio card when audio controls are unavailable', async () => {
    const wrapper = mountModule({ showAudioControls: false });
    await flush();
    expect(wrapper.text()).not.toContain('Show Audio Controls');
    await wrapper.setProps({ showAudioControls: true });
    expect(wrapper.text()).toContain('Show Audio Controls');
  });
});
