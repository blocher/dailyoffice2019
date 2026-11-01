/*
  API addresses shared by the pages and the sync engine
  =====================================================
  The sync engine downloads exactly what a page would ask for, so both build
  their addresses here.
*/

export function apiUrl(path) {
  return `${import.meta.env.VITE_API_URL || '/'}api/v1/${path}`;
}

// The API's date form: 2026-11-2 (no padding).
export function apiDate(date) {
  return `${date.getFullYear()}-${date.getMonth() + 1}-${date.getDate()}`;
}

export function withDefaultTranslation(settings) {
  const copy = { ...(settings || {}) };
  if (!copy.bible_translation) copy.bible_translation = 'esv';
  return copy;
}

export function settingsQuery(settings) {
  return Object.keys(settings)
    .map((key) => key + '=' + settings[key])
    .join('&');
}

const OFFICE_COLLECT_NAMES = {
  morning_prayer: 'Morning Prayer',
  midday_prayer: 'Midday Prayer',
  evening_prayer: 'Evening Prayer',
  compline: 'Compline',
};

// Extra collects chosen for one daily office, as the API takes them.
export function extraCollectsFor(serviceType, office, extraCollects) {
  if (serviceType !== 'office' || !extraCollects) return '';
  const list = extraCollects[OFFICE_COLLECT_NAMES[office]];
  return Array.isArray(list) ? list.join(',') : '';
}

export function officeUrl({
  serviceType,
  office,
  date,
  settings,
  extraCollects,
}) {
  return (
    apiUrl(`${serviceType}/${office}/`) +
    apiDate(date) +
    '?' +
    settingsQuery(withDefaultTranslation(settings)) +
    '&extra_collects=' +
    extraCollectsFor(serviceType, office, extraCollects)
  );
}

export function readingsUrl({ date, translation, psalms, style, settings }) {
  return (
    apiUrl(`readings/${apiDate(date)}`) +
    `?translation=${translation}&psalms=${psalms}&style=${style}&` +
    settingsQuery(settings || {})
  );
}

export function dayUrl(date) {
  return apiUrl(`calendar/${apiDate(date)}`);
}

export function monthUrl(year, month) {
  return apiUrl(`calendar/${year}-${month}`);
}

export const DAILY_OFFICES = [
  'morning_prayer',
  'midday_prayer',
  'evening_prayer',
  'compline',
];

export const FAMILY_OFFICES = [
  'morning_prayer',
  'midday_prayer',
  'early_evening_prayer',
  'close_of_day_prayer',
];
