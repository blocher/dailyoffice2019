/*
  Office audio addresses for CarPlay and Android Auto
  ===================================================
  In the car the apps play an office without this page: the native side asks
  the API for the audio track itself (ios/App/App/Car/, android/.../car/).
  It must ask with exactly the address this page would, so it gets the same
  track (the same cached clips, never newly generated audio) for the
  listener's settings and extra collects.

  So the page saves those addresses as templates in Capacitor Preferences
  ("nativeAudioRequests"), with "{date}" (and for readings "{kind}") where
  the native side fills in the day:

    { version: 1,
      offices: { "office/compline": ".../api/v1/office/compline/{date}?...&include_audio_links=true", ... },
      readings: ".../api/v1/readings_audio/{kind}/{date}?translation=esv&...&include_audio_links=true" }

  Office.vue and Readings.vue save them whenever they build their own, and
  the store when settings change. The addresses are built with the same
  helpers the pages use (offline/urls.js), so they can't drift apart.
*/
import { Capacitor } from '@capacitor/core';
import { DynamicStorage } from './storage';
import {
  DAILY_OFFICES,
  FAMILY_OFFICES,
  apiDate,
  apiUrl,
  officeUrl,
} from '@/offline/urls';

export const NATIVE_AUDIO_REQUESTS_KEY = 'nativeAudioRequests';

// A day no real request is for, so its date can be found and replaced.
const MARK_DATE = new Date(2000, 0, 1);
const MARK = apiDate(MARK_DATE);

let lastSaved = null;

async function storedJson(key) {
  try {
    return JSON.parse((await DynamicStorage.getItem(key)) || 'null');
  } catch {
    return null;
  }
}

function template(url) {
  return url.replace(`/${MARK}?`, '/{date}?');
}

/*
  The templates for these settings, as Office.vue and Readings.vue would
  build each request. `extraCollects` and `readings` default to what the
  pages keep in storage.
*/
export async function nativeAudioRequests(
  settings,
  { extraCollects, readings } = {}
) {
  const chosenCollects =
    extraCollects === undefined
      ? await storedJson('extraCollects')
      : extraCollects;
  const offices = {};
  for (const [serviceType, list] of [
    ['office', DAILY_OFFICES],
    ['family', FAMILY_OFFICES],
  ]) {
    for (const office of list) {
      offices[`${serviceType}/${office}`] = template(
        officeUrl({
          serviceType,
          office,
          date: MARK_DATE,
          settings,
          extraCollects: chosenCollects,
        }) + '&include_audio_links=true'
      );
    }
  }

  // As Readings.vue chooses them: the page's own choice, else the settings.
  let translation = await DynamicStorage.getItem('readings_translation');
  if (!translation || translation === 'undefined') {
    translation = settings?.bible_translation || 'esv';
  }
  const choice = readings || {
    translation,
    psalms:
      (await DynamicStorage.getItem('psalms_translation')) ||
      settings?.language_style,
    style:
      (await DynamicStorage.getItem('psalm_style')) || settings?.psalm_style,
    psalter: (await DynamicStorage.getItem('psalter')) || settings?.psalter,
  };
  const query = new window.URLSearchParams({
    translation: choice.translation,
    psalms: choice.psalms,
    style: choice.style,
    psalter: choice.psalter,
    position: '0',
    include_audio_links: 'true',
  });
  return {
    version: 1,
    offices,
    readings: `${apiUrl('readings_audio/')}{kind}/{date}?${query}`,
  };
}

// Saves the templates for the native side. Best-effort, native apps only.
export async function saveNativeAudioRequests(settings, options = {}) {
  if (!Capacitor.isNativePlatform() || !settings) return;
  try {
    const value = JSON.stringify(await nativeAudioRequests(settings, options));
    if (value === lastSaved) return;
    await DynamicStorage.setItem(NATIVE_AUDIO_REQUESTS_KEY, value);
    lastSaved = value;
  } catch {
    // The car falls back to the default settings until the next save.
  }
}
