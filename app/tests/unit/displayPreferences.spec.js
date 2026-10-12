// @vitest-environment jsdom

import { mount } from '@vue/test-utils';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import DisplaySettings from '@/components/DisplaySettings.vue';
import UiKit from '@/ui';
import {
  DEFAULT_FONT_SIZE,
  displayState,
  fontSizePercent,
  loadDisplayPreferences,
  nextFontSize,
  setReadingFont,
  setTheme,
} from '@/helpers/displayPreferences';
import { DynamicStorage } from '@/helpers/storage';

vi.mock('@/helpers/storage', () => ({
  DynamicStorage: { getItem: vi.fn(), setItem: vi.fn() },
}));

function stubStorage(values) {
  DynamicStorage.getItem.mockImplementation(async (key) => values[key] ?? null);
}

describe('display preferences', () => {
  beforeEach(() => {
    DynamicStorage.setItem.mockReset().mockResolvedValue();
    document.documentElement.className = '';
    delete document.documentElement.dataset.readingFont;
    window.matchMedia = vi.fn().mockReturnValue({
      matches: false,
      addEventListener: vi.fn(),
    });
  });

  it('keeps stored preferences from earlier versions of the app', async () => {
    stubStorage({
      'user-theme': 'dark',
      fontSize: '30',
      audioEnabled: 'false',
    });
    await loadDisplayPreferences();
    expect(displayState.theme).toBe('dark');
    expect(document.documentElement.classList.contains('dark')).toBe(true);
    expect(displayState.fontSize).toBe(30);
    expect(displayState.audioEnabled).toBe(false);
    expect(displayState.readingFont).toBe('caslon');
    expect(
      document.documentElement.style.getPropertyValue('--main-font-size')
    ).toBe('30px');
  });

  it('follows the device when no theme is stored', async () => {
    stubStorage({});
    window.matchMedia.mockReturnValue({
      matches: true,
      addEventListener: vi.fn(),
    });
    await loadDisplayPreferences();
    expect(displayState.theme).toBe('auto');
    expect(displayState.resolvedTheme).toBe('dark');
  });

  it('applies sepia and a reading typeface, and saves them', async () => {
    stubStorage({});
    await loadDisplayPreferences();
    await setTheme('sepia');
    await setReadingFont('baskerville');
    expect(document.documentElement.classList.contains('sepia')).toBe(true);
    expect(document.documentElement.dataset.readingFont).toBe('baskerville');
    expect(DynamicStorage.setItem).toHaveBeenCalledWith('user-theme', 'sepia');
    expect(DynamicStorage.setItem).toHaveBeenCalledWith(
      'readingFont',
      'baskerville'
    );
    await setReadingFont('caslon');
    expect(document.documentElement.dataset.readingFont).toBeUndefined();
  });

  it('steps text size along fixed notches and reports it against the default', () => {
    expect(nextFontSize(DEFAULT_FONT_SIZE, 1)).toBe(26);
    expect(nextFontSize(DEFAULT_FONT_SIZE, -1)).toBe(22);
    // An old free-form size from the previous slider snaps to the next notch.
    expect(nextFontSize(25, 1)).toBe(26);
    expect(fontSizePercent(DEFAULT_FONT_SIZE)).toBe(100);
    expect(fontSizePercent(36)).toBe(150);
  });

  it('renders every theme and typeface choice', async () => {
    stubStorage({});
    await loadDisplayPreferences();
    const wrapper = mount(DisplaySettings, { global: { plugins: [UiKit] } });
    const text = wrapper.text();
    for (const label of ['Auto', 'Light', 'Sepia', 'Dark']) {
      expect(text).toContain(label);
    }
    for (const label of ['Caslon', 'Baskerville', 'Black Letter']) {
      expect(text).toContain(label);
    }
    expect(text).toContain('Audio player');

    await wrapper.setProps({ showAudio: false });
    expect(wrapper.text()).not.toContain('Audio player');
  });
});
