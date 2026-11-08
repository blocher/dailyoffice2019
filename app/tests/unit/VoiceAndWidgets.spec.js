import { describe, expect, it, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import VoiceAndWidgets from '../../src/views/VoiceAndWidgets.vue';
import UiKit from '../../src/ui';

const { getPlatform } = vi.hoisted(() => ({
  getPlatform: vi.fn(() => 'web'),
}));

vi.mock('@capacitor/core', () => ({
  Capacitor: { getPlatform },
}));

function mountPage(platform) {
  getPlatform.mockReturnValue(platform);
  return mount(VoiceAndWidgets, { global: { plugins: [UiKit] } });
}

describe('VoiceAndWidgets', () => {
  it('shows only the iPhone guide in the iOS app', () => {
    const wrapper = mountPage('ios');
    expect(wrapper.find('h1').text()).toBe('Siri & Widgets');
    expect(wrapper.text()).toContain('Play Midday Prayer on The Daily Office');
    expect(wrapper.text()).toContain('without opening the app');
    expect(wrapper.text()).toContain('Lock Screen widgets');
    expect(wrapper.text()).toContain('CarPlay');
    expect(wrapper.text()).not.toContain('Android Auto');
    expect(wrapper.find('.voice-guide__platform').exists()).toBe(false);
  });

  it('shows only the Android guide in the Android app', () => {
    const wrapper = mountPage('android');
    expect(wrapper.find('h1').text()).toBe('Google & Widgets');
    expect(wrapper.text()).toContain('Play Evening Prayer on Daily Office');
    expect(wrapper.text()).toContain('Open Pray now on Daily Office');
    expect(wrapper.text()).toContain('Android Auto');
    expect(wrapper.text()).not.toContain('Lock Screen');
    expect(wrapper.find('.voice-guide__platform').exists()).toBe(false);
  });

  it('lets the website switch between the two apps', async () => {
    const wrapper = mountPage('web');
    expect(wrapper.find('.voice-guide__platform').exists()).toBe(true);
    expect(wrapper.find('h1').text()).toBe('Siri & Widgets');
    const android = wrapper
      .findAll('.voice-guide__platform button')
      .find((button) => button.text().includes('Android'));
    await android.trigger('click');
    expect(wrapper.find('h1').text()).toBe('Google & Widgets');
    expect(wrapper.text()).toContain('Android app');
  });
});
