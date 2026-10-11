import { describe, expect, it } from 'vitest';
import { decodeSettingsString } from '../../src/helpers/decodeSettingsString';
import { createSettingsString } from '../../src/helpers/createSettingsString';

const abbreviations = [
  {
    setting_name: 'reading_cycle',
    options: [
      { option_value: '1', abbreviation: 'A' },
      { option_value: '2', abbreviation: 'B' },
    ],
  },
  {
    setting_name: 'apocrypha_readings',
    options: [
      { option_value: 'appointed', abbreviation: 'A' },
      { option_value: 'alternate', abbreviation: 'B' },
    ],
  },
];

describe('appended alternate-reading share setting', () => {
  it('decodes older links without consuming the new setting', () => {
    expect(decodeSettingsString('B', abbreviations)).toEqual([
      { settingName: 'reading_cycle', value: '2' },
    ]);
  });

  it('round-trips the opt-in and default settings', () => {
    for (const value of ['appointed', 'alternate']) {
      const settings = { reading_cycle: '1', apocrypha_readings: value };
      const encoded = createSettingsString(settings, abbreviations);
      const decoded = Object.fromEntries(
        decodeSettingsString(encoded, abbreviations).map((item) => [
          item.settingName,
          item.value,
        ])
      );
      expect(decoded).toEqual(settings);
    }
  });
});
