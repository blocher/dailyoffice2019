import { describe, expect, it } from 'vitest';
import {
  buildSettingSearchText,
  createNormalizedApiSetting,
  matchesSettingSearch,
  resolveSettingUiMetadata,
} from '../../src/helpers/settingsUiMetadata';

describe('settingsUiMetadata', () => {
  it('uses fallback metadata when API metadata is missing', () => {
    const metadata = resolveSettingUiMetadata({
      name: 'reading_audio',
      setting_type: 1,
    });

    expect(metadata.category).toBe('Audio');
    expect(metadata.priority).toBe(40);
    expect(metadata.keywords).toContain('scripture audio');
    expect(metadata.helpShort).toContain('scripture content audio');
  });

  it('prefers API metadata when present', () => {
    const metadata = resolveSettingUiMetadata({
      name: 'reading_audio',
      setting_type: 1,
      ui_category: 'Custom Category',
      ui_priority: 3,
      ui_keywords: ['custom keyword'],
      ui_help_short: 'Custom helper',
    });

    expect(metadata.category).toBe('Custom Category');
    expect(metadata.priority).toBe(3);
    expect(metadata.keywords).toContain('custom keyword');
    expect(metadata.helpShort).toBe('Custom helper');
  });

  it('builds normalized settings with source/site metadata and persist handler', () => {
    const setting = createNormalizedApiSetting(
      {
        name: 'psalter',
        site_name: 'Daily Office',
        setting_type: 1,
        title: 'Psalter Cycle',
        options: [],
      },
      () => Promise.resolve()
    );

    expect(setting.source).toBe('api');
    expect(setting.site).toBe('Daily Office');
    expect(setting.category).toBe('Readings');
    expect(typeof setting.persist).toBe('function');
  });

  it('matches search against descriptions, options, and keywords', () => {
    const normalized = createNormalizedApiSetting(
      {
        name: 'reading_length',
        site_name: 'Daily Office',
        setting_type: 1,
        title: 'Reading Length',
        description: '<p>Use full or abbreviated readings.</p>',
        options: [
          {
            name: 'Abbreviated',
            description: 'Suggested abbreviations when available',
            value: 'abbreviated',
          },
        ],
      },
      () => Promise.resolve()
    );

    expect(buildSettingSearchText(normalized)).toContain('abbreviated');
    expect(matchesSettingSearch(normalized, 'abbreviated')).toBe(true);
    expect(matchesSettingSearch(normalized, 'full readings')).toBe(true);
    expect(matchesSettingSearch(normalized, 'canticles')).toBe(false);
  });
});
