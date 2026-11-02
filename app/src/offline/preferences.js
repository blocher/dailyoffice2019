/*
  Offline preferences (this device)
  =================================
    days          how many days ahead to keep: 0 (off), 3, 7, 14, 30, 60.
                  Unset, it is 30 in the apps and an installed web app, and
                  7 in a browser tab (30 there too once the installed web
                  app has run: the two share storage and the plan, and each
                  would prune what the other downloads).
    family        'on' (the default) or 'off': Family Prayer for each day
    readings      'on' (the default) or 'off': the day's readings
    audio         download audio for today and tomorrow (opt-in)
    audioOffices  which daily offices' audio to download
*/
import { reactive } from 'vue';
import { Capacitor } from '@capacitor/core';
import { DynamicStorage } from '@/helpers/storage';

export const DAY_CHOICES = [0, 3, 7, 14, 30, 60];
export const AUDIO_DAYS = 2;
export const AUDIO_OFFICE_CHOICES = [
  'morning_prayer',
  'midday_prayer',
  'evening_prayer',
  'compline',
];

const KEYS = {
  days: 'offline_days',
  family: 'offline_family',
  readings: 'offline_readings',
  audio: 'offline_audio',
  audioOffices: 'offline_audio_offices',
};
const INSTALLED_KEY = 'offline_installed';
let installedBefore = false;

export const offlinePrefs = reactive({
  loaded: false,
  days: null,
  family: 'on',
  readings: 'on',
  audio: false,
  audioOffices: ['morning_prayer', 'evening_prayer'],
});

export function isInstalledApp() {
  if (Capacitor.isNativePlatform()) return true;
  try {
    return (
      window.matchMedia?.('(display-mode: standalone)')?.matches ||
      window.matchMedia?.('(display-mode: window-controls-overlay)')?.matches ||
      window.navigator.standalone === true
    );
  } catch {
    return false;
  }
}

export function defaultDays() {
  return isInstalledApp() || installedBefore ? 30 : 7;
}

export function effectiveDays() {
  return offlinePrefs.days ?? defaultDays();
}

export async function loadOfflinePrefs() {
  try {
    const [days, family, readings, audio, audioOffices] = await Promise.all(
      Object.values(KEYS).map((key) => DynamicStorage.getItem(key))
    );
    const parsedDays =
      days === null || days === '' || days === undefined ? null : Number(days);
    offlinePrefs.days = DAY_CHOICES.includes(parsedDays) ? parsedDays : null;
    // Only a choice of 'off' is kept: Family Prayer and the readings are on
    // unless turned off (before 4.1, Family Prayer's default was 'auto', on
    // once it had been prayed).
    offlinePrefs.family = family === 'off' ? 'off' : 'on';
    offlinePrefs.readings = readings === 'off' ? 'off' : 'on';
    offlinePrefs.audio = audio === 'true';
    installedBefore = (await DynamicStorage.getItem(INSTALLED_KEY)) === 'true';
    if (!installedBefore && isInstalledApp() && !Capacitor.isNativePlatform()) {
      installedBefore = true;
      await DynamicStorage.setItem(INSTALLED_KEY, 'true');
    }
    try {
      const offices = JSON.parse(audioOffices || 'null');
      if (Array.isArray(offices)) {
        offlinePrefs.audioOffices = offices.filter((o) =>
          AUDIO_OFFICE_CHOICES.includes(o)
        );
      }
    } catch {
      // Keep the default.
    }
  } finally {
    offlinePrefs.loaded = true;
  }
}

export async function setOfflinePref(name, value) {
  offlinePrefs[name] = value;
  const stored =
    name === 'audioOffices' ? JSON.stringify(value) : String(value);
  await DynamicStorage.setItem(KEYS[name], stored);
}
