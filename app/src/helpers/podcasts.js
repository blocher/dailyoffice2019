/*
  Podcasts
  ========
  The Podcasts page stays at /podcasts, but the menu and the audio player
  only point to it once the feeds are listed in the podcast directories, so
  Subscribe opens each app's own show page instead of asking for a feed URL.
  (See "Publishing to podcast directories" in README.md.)
*/
export const PODCASTS_PROMOTED = false;

/*
  Podcast apps that subscribe to an RSS feed by its address, with a one-tap
  link where the app has one and the steps to add it by hand.

  Documented: Overcast (overcast://x-callback-url/add), Pocket Casts
  (pktc://subscribe/<feed without scheme>), AntennaPod (its https deeplink,
  which falls back to instructions without the app), Apple Podcasts
  (podcast://<feed without scheme>). Castro (castros://subscribe/) and
  Podcast Addict (podcastaddict://) are the schemes the apps register but
  aren't documented; the steps cover them if a link does nothing.
*/
export function podcastApps(feedUrl, { title = '', appleUrl = '' } = {}) {
  const bare = feedUrl.replace(/^https?:\/\//, '');
  const encoded = encodeURIComponent(feedUrl);
  return [
    {
      id: 'apple',
      name: 'Apple Podcasts',
      platforms: 'iPhone, iPad, Mac',
      icon: 'apple',
      href: appleUrl || `podcast://${bare}`,
      steps: [
        'In Library, tap the ⋯ button and choose Follow a Show by URL. On a Mac, choose File › Follow a Show by URL.',
        'Paste the link and tap Follow.',
      ],
    },
    {
      id: 'overcast',
      name: 'Overcast',
      platforms: 'iPhone, iPad',
      icon: 'podcast',
      href: `overcast://x-callback-url/add?url=${encoded}`,
      steps: [
        'Tap + at the top, then Add URL.',
        'Paste the link and tap Done.',
      ],
    },
    {
      id: 'pocket_casts',
      name: 'Pocket Casts',
      platforms: 'iPhone, Android',
      icon: 'podcast',
      href: `pktc://subscribe/${bare}`,
      steps: [
        'Tap Search (Discover), paste the link into the search field, and search.',
        'Tap the show, then Follow.',
      ],
    },
    {
      id: 'castro',
      name: 'Castro',
      platforms: 'iPhone',
      icon: 'podcast',
      href: `castros://subscribe/${bare}`,
      steps: [
        'Open Library and tap Search, or the + button.',
        'Paste the link, then tap the show and Subscribe.',
      ],
    },
    {
      id: 'antennapod',
      name: 'AntennaPod',
      platforms: 'Android',
      icon: 'android',
      href: `https://antennapod.org/deeplink/subscribe?url=${encoded}&title=${encodeURIComponent(title)}`,
      steps: [
        'Tap + (Add podcast), then Add podcast by RSS address.',
        'Paste the link and tap Confirm, then Subscribe.',
      ],
    },
    {
      id: 'podcast_addict',
      name: 'Podcast Addict',
      platforms: 'Android',
      icon: 'android',
      href: `podcastaddict://${bare}`,
      steps: ['Tap +, then RSS feed.', 'Paste the link and tap Add.'],
    },
  ];
}

// The one setting group the audio can't follow: it is read only in English,
// from the ESV or the KJV (audio_available on the server).
export const AUDIO_SETTINGS = {
  bible_translation: ['esv', 'kjv'],
  display_language: ['english'],
};

function pick(value, allowed, fallback) {
  return allowed.includes(value) ? value : fallback;
}

/*
  The settings a custom podcast starts from: a snapshot of the reader's own
  (the Vuex settings), limited to the keys the server takes and to the
  translations the audio is read in. Returns { settings, adjusted }, where
  adjusted names the settings that had to change.
*/
export function snapshotSettings(options, isReadings, current = {}) {
  const audio = { ...AUDIO_SETTINGS, ...(options.audio || {}) };
  const adjusted = [];
  if (isReadings) {
    const { defaults, choices } = options.readings_settings;
    const wanted = {
      translation: current.bible_translation,
      psalms: current.psalm_translation,
      style: current.psalm_style,
      psalter: current.psalter,
    };
    const settings = {};
    for (const key of options.readings_settings.keys) {
      settings[key] = pick(wanted[key], choices[key], defaults[key]);
    }
    if (
      current.bible_translation &&
      current.bible_translation !== settings.translation
    ) {
      adjusted.push('translation');
    }
    return { settings, adjusted };
  }
  const { keys, defaults } = options.office_settings;
  const settings = {};
  for (const key of keys) {
    const value = current[key];
    settings[key] = typeof value === 'string' && value ? value : defaults[key];
  }
  for (const [key, allowed] of Object.entries(audio)) {
    if (key in settings && !allowed.includes(settings[key])) {
      settings[key] = pick(defaults[key], allowed, allowed[0]);
      adjusted.push(key);
    }
  }
  return { settings, adjusted };
}

/*
  The settings rows for the Customize sheet: only the keys a custom podcast
  takes, copied so choosing never touches the shared list, with the audio
  settings limited to what can be read aloud.
*/
export function customizableSettings(availableSettings, options) {
  const keys = new Set(options.office_settings.keys);
  const audio = { ...AUDIO_SETTINGS, ...(options.audio || {}) };
  return (availableSettings || [])
    .filter((setting) => keys.has(setting.name))
    .map((setting) => {
      const allowed = audio[setting.name];
      const settingOptions = (setting.options || []).filter(
        (option) => !allowed || allowed.includes(option.value)
      );
      return {
        ...setting,
        active: undefined,
        options: settingOptions.map((option) => ({ ...option })),
      };
    });
}

// The Readings page's choices, as rows for SettingRow.
export function readingsSettingRows(options) {
  const names = {
    translation: {
      title: 'Bible translation',
      labels: {
        esv: 'English Standard Version (ESV)',
        kjv: 'King James Version (KJV)',
      },
    },
    psalms: {
      title: 'Psalter',
      labels: {
        contemporary: 'Contemporary (Renewed Coverdale)',
        traditional: 'Traditional (Coverdale)',
      },
    },
    style: {
      title: 'Psalm style',
      labels: {
        whole_verse: 'Antiphonally by whole verse',
        half_verse: 'Antiphonally by half verse',
        unison: 'In unison',
      },
    },
    psalter: {
      title: 'Psalm cycle',
      labels: { 60: '60-day cycle', 30: '30-day cycle' },
    },
  };
  const { keys, choices, defaults } = options.readings_settings;
  return keys.map((key) => {
    const values = [...choices[key]].sort((a, b) =>
      a === defaults[key] ? -1 : b === defaults[key] ? 1 : 0
    );
    return {
      name: key,
      title: names[key]?.title || key,
      options: values.map((value) => ({
        value,
        name: names[key]?.labels?.[value] || value,
      })),
    };
  });
}
