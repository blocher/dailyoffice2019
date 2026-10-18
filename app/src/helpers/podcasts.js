import { onBeforeUnmount, ref } from 'vue';

/*
  Podcast apps that subscribe to an RSS feed by its address, with a one-tap
  link where the app has one and the steps to add it by hand.

  Each app also has `install`, its store pages ({ ios, android }), for when
  the link does nothing because the app isn't installed (see watchAppOpen).

  Documented: Overcast (overcast://x-callback-url/add), Pocket Casts
  (pktc://subscribe/<feed without scheme>), AntennaPod (its https deeplink,
  which falls back to instructions without the app), Apple Podcasts
  (podcast://<feed without scheme>). Castro (castros://subscribe/) and
  Podcast Addict (podcastaddict://) are the schemes the apps register but
  aren't documented; the steps cover them if a link does nothing.
*/
const APP_STORE = (path) => `https://apps.apple.com/app/${path}`;
const PLAY_STORE = (id) =>
  `https://play.google.com/store/apps/details?id=${id}`;

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
      install: { ios: APP_STORE('apple-podcasts/id525463029') },
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
      install: { ios: APP_STORE('overcast/id888422857') },
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
      install: {
        ios: APP_STORE('pocket-casts-podcast-player/id414834813'),
        android: PLAY_STORE('au.com.shiftyjelly.pocketcasts'),
      },
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
      install: { ios: APP_STORE('castro-podcast-player/id1080840241') },
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
      install: { android: PLAY_STORE('de.danoeh.antennapod') },
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
      install: { android: PLAY_STORE('com.bambuna.podcastaddict') },
      steps: ['Tap +, then RSS feed.', 'Paste the link and tap Add.'],
    },
  ];
}

// Whether the link opens an app by its own scheme, which does nothing at all
// when the app isn't installed (an https link falls back to a web page).
export function opensApp(href) {
  return !/^https?:/i.test(href || '');
}

// 'ios', 'android', or '' (a computer, or we can't tell). iPads report a Mac
// user agent, so a touch screen on a "Mac" counts as iOS.
export function devicePlatform(nav = globalThis.navigator) {
  const agent = nav?.userAgent || '';
  if (/android/i.test(agent)) return 'android';
  if (/iphone|ipad|ipod/i.test(agent)) return 'ios';
  if (/macintosh/i.test(agent) && nav?.maxTouchPoints > 1) return 'ios';
  return '';
}

/*
  The store pages to offer when an app didn't open: the one for this device,
  or every one the app has on a computer. [{ platform, label, href }]
*/
export function installLinks(app, platform = devicePlatform()) {
  const labels = { ios: 'App Store', android: 'Google Play' };
  return Object.entries(app.install || {})
    .filter(([store]) => !platform || store === platform)
    .map(([store, href]) => ({ platform: store, label: labels[store], href }));
}

/*
  Call when a podcast app's link is followed. If the app opens, the page is
  hidden or loses focus; if neither happens within `delay`, the app most
  likely isn't installed and onMissing runs. Returns a function that stops
  watching.
*/
export function watchAppOpen(onMissing, { delay = 1500, win = window } = {}) {
  const doc = win.document;
  let timer = null;
  const stop = () => {
    win.clearTimeout(timer);
    win.removeEventListener('blur', stop);
    win.removeEventListener('pagehide', stop);
    doc.removeEventListener('visibilitychange', onVisibility);
  };
  const onVisibility = () => {
    if (doc.visibilityState === 'hidden') stop();
  };
  win.addEventListener('blur', stop);
  win.addEventListener('pagehide', stop);
  doc.addEventListener('visibilitychange', onVisibility);
  timer = win.setTimeout(() => {
    stop();
    if (doc.visibilityState !== 'hidden') onMissing();
  }, delay);
  return stop;
}

/*
  For a component with podcast app links: call follow(app) when one is
  followed; missing is the id of the app that didn't open, if any, until the
  next link is followed or reset() is called.
*/
export function useMissingApp() {
  const missing = ref(null);
  let stop = null;
  function reset() {
    stop?.();
    stop = null;
    missing.value = null;
  }
  function follow(app) {
    reset();
    if (!opensApp(app.href)) return;
    stop = watchAppOpen(() => {
      missing.value = app.id;
    });
  }
  onBeforeUnmount(() => stop?.());
  return { missing, follow, reset };
}

// The settings the audio can't follow (AUDIO_SETTINGS on the server, which
// sends them as options.audio): it is read only in English, in traditional or
// contemporary language, from the ESV or the KJV, with the Coverdale or
// Renewed Coverdale Psalter.
export const AUDIO_SETTINGS = {
  display_language: ['english'],
  language_style: ['contemporary', 'traditional'],
  bible_translation: ['esv', 'kjv'],
  psalm_translation: ['contemporary', 'traditional'],
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
    for (const key of ['translation', 'psalms']) {
      if (wanted[key] && wanted[key] !== settings[key]) adjusted.push(key);
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
