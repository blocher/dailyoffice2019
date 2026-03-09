const SETTING_TYPE_DEFAULTS = {
  1: { category: 'Prayer', priority: 120 },
  2: { category: 'More Options', priority: 520 },
  3: { category: 'Expert', priority: 820 },
};

export const SETTINGS_UI_FALLBACK_METADATA = {
  psalter: {
    category: 'Readings',
    priority: 10,
    keywords: ['psalms', 'cycle', 'morning prayer', 'evening prayer'],
  },
  reading_cycle: {
    category: 'Readings',
    priority: 20,
    keywords: ['lectionary', 'one year', 'two year'],
  },
  reading_length: {
    category: 'Readings',
    priority: 30,
    keywords: ['abbreviated', 'full readings'],
  },
  reading_audio: {
    category: 'Audio',
    priority: 40,
    keywords: ['esv', 'scripture audio', 'player'],
    helpShort: 'Controls whether scripture content audio is included.',
  },
  canticle_rotation: {
    category: 'Prayer',
    priority: 50,
    keywords: ['canticles', 'seasonal', 'traditional'],
  },
  lectionary: {
    category: 'Calendar',
    priority: 180,
    keywords: ['sunday', 'holy day', 'eucharistic readings'],
  },
  confession: {
    category: 'Prayer',
    priority: 190,
    keywords: ['intro', 'exhortation'],
  },
  absolution: {
    category: 'Prayer',
    priority: 200,
    keywords: ['priest', 'lay', 'deacon'],
  },
  morning_prayer_invitatory: {
    category: 'Prayer',
    priority: 210,
    keywords: ['venite', 'jubilate', 'pascha nostrum'],
  },
  reading_headings: {
    category: 'Readings',
    priority: 220,
    keywords: ['esv headings', 'headings'],
  },
  language_style: {
    category: 'Language',
    priority: 230,
    keywords: ['traditional', 'contemporary', 'our father', 'kyrie'],
  },
  national_holidays: {
    category: 'Calendar',
    priority: 240,
    keywords: ['us', 'canada', 'holiday collects'],
  },
  suffrages: {
    category: 'Prayer',
    priority: 250,
    keywords: ['evening prayer', 'set a', 'set b'],
  },
  collects: {
    category: 'Prayer',
    priority: 260,
    keywords: ['additional collects', 'fixed', 'rotating'],
  },
  pandemic_prayers: {
    category: 'Prayer',
    priority: 270,
    keywords: ['pandemic', 'special collects'],
  },
  mp_great_litany: {
    category: 'Litany',
    priority: 280,
    keywords: ['morning prayer litany', 'wednesday', 'friday', 'sunday'],
  },
  ep_great_litany: {
    category: 'Litany',
    priority: 290,
    keywords: ['evening prayer litany', 'wednesday', 'friday', 'sunday'],
  },
  general_thanksgiving: {
    category: 'Conclusion',
    priority: 300,
    keywords: ['thanksgiving'],
  },
  chrysostom: {
    category: 'Conclusion',
    priority: 310,
    keywords: ['group prayer', 'st john chrysostom'],
  },
  grace: {
    category: 'Conclusion',
    priority: 320,
    keywords: ['conclusion', 'rotating grace'],
  },
  o_antiphons: {
    category: 'Calendar',
    priority: 330,
    keywords: ['advent', 'seasonal', 'o come o come emmanuel'],
  },
  family_readings: {
    category: 'Readings',
    priority: 10,
    keywords: ['family prayer', 'brief', 'long'],
  },
  family_reading_audio: {
    category: 'Audio',
    priority: 40,
    keywords: ['family prayer audio', 'esv'],
    helpShort: 'Controls whether scripture content audio is included.',
  },
  family_collect: {
    category: 'Prayer',
    priority: 50,
    keywords: ['collect', 'time of day', 'day of week', 'day of year'],
  },
  'family-opening-sentence': {
    category: 'Prayer',
    priority: 190,
    keywords: ['opening sentence', 'seasonal'],
  },
  'family-creed': {
    category: 'Prayer',
    priority: 200,
    keywords: ['apostles creed'],
  },
};

function asTrimmedString(value) {
  if (typeof value !== 'string') {
    return null;
  }
  const result = value.trim();
  return result.length ? result : null;
}

function sanitizeHtml(input) {
  if (!input) {
    return '';
  }
  return String(input)
    .replace(/<[^>]*>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function normalizePriority(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function normalizeKeywords(input) {
  if (Array.isArray(input)) {
    return input
      .map((keyword) => asTrimmedString(keyword))
      .filter((keyword) => keyword !== null);
  }
  const value = asTrimmedString(input);
  if (!value) {
    return [];
  }
  return value
    .split(',')
    .map((part) => asTrimmedString(part))
    .filter((part) => part !== null);
}

function getSettingTypeDefaults(settingType) {
  return SETTING_TYPE_DEFAULTS[settingType] || SETTING_TYPE_DEFAULTS[2];
}

export function resolveSettingUiMetadata(setting) {
  const fallback = SETTINGS_UI_FALLBACK_METADATA[setting.name] || {};
  const defaults = getSettingTypeDefaults(setting.setting_type);

  const category =
    asTrimmedString(setting.ui_category) ||
    fallback.category ||
    defaults.category;

  const priority =
    normalizePriority(setting.ui_priority) ??
    fallback.priority ??
    defaults.priority;

  const keywords = Array.from(
    new Set([
      ...normalizeKeywords(fallback.keywords),
      ...normalizeKeywords(setting.ui_keywords),
    ])
  );

  const helpShort =
    asTrimmedString(setting.ui_help_short) || fallback.helpShort || '';

  return {
    category,
    priority,
    keywords,
    helpShort,
  };
}

export function createNormalizedApiSetting(setting, persist) {
  const metadata = resolveSettingUiMetadata(setting);
  return {
    source: 'api',
    site: setting.site_name || 'global',
    persist,
    ...metadata,
    ...setting,
  };
}

export function buildSettingSearchText(setting) {
  const pieces = [
    setting.title,
    setting.description,
    setting.helpShort,
    ...(setting.keywords || []),
    ...(setting.options || []).flatMap((option) => [
      option.name,
      option.description,
      option.value,
    ]),
  ];
  return sanitizeHtml(pieces.join(' ')).toLowerCase();
}

export function matchesSettingSearch(setting, query) {
  const normalizedQuery = asTrimmedString(query)?.toLowerCase();
  if (!normalizedQuery) {
    return true;
  }
  return buildSettingSearchText(setting).includes(normalizedQuery);
}

export function slugifyLabel(value) {
  return String(value || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}
