/*
  Display preferences
  ===================
  Theme, text size, reading face, rubric style, and whether audio controls
  show. One
  reactive store shared by the header's Display panel, the Settings page, and
  the office page, so a change in one place shows everywhere at once.
  Values persist through DynamicStorage under the same keys the app has
  always used ('user-theme', 'fontSize', 'audioEnabled') plus 'readingFont'
  and 'rubricStyle'.
*/
import { reactive } from 'vue';
import { DynamicStorage } from '@/helpers/storage';
import { refreshSeasonAccent } from '@/helpers/seasonAccent';

export const THEMES = [
  { value: 'auto', label: 'Auto', icon: 'contrast', title: 'Match device' },
  { value: 'light', label: 'Light', icon: 'sun' },
  { value: 'sepia', label: 'Sepia', icon: 'book' },
  { value: 'dark', label: 'Dark', icon: 'moon' },
];

export const DEFAULT_FONT_SIZE = 24;
export const FONT_SIZES = [16, 18, 20, 22, 24, 26, 28, 31, 34, 38, 42];

export const READING_FONTS = [
  {
    value: 'caslon',
    label: 'Caslon',
    note: 'The 2019 Prayer Book',
    family: "'Adobe Caslon Pro', Georgia, serif",
  },
  {
    value: 'garamond',
    label: 'Garamond',
    note: 'Old style, as in the 1928 and 1979 books',
    family: "'EB Garamond', Georgia, serif",
  },
  {
    value: 'baskerville',
    label: 'Baskerville',
    note: 'Cambridge Prayer Book, 1760',
    family: "'Libre Baskerville', Baskerville, Georgia, serif",
  },
  {
    value: 'blackletter',
    label: 'Black Letter',
    note: 'The books of 1549–1662',
    family: "'Grenze Gotisch', serif",
  },
  {
    value: 'sans',
    label: 'Sans-serif',
    note: 'Gill Sans, as in Common Worship',
    family: "'Gill Sans', 'Gill Sans MT', 'Source Sans 3', sans-serif",
  },
  {
    value: 'legible',
    label: 'Hyperlegible',
    note: 'Designed for low vision',
    family: "'Atkinson Hyperlegible Next', sans-serif",
  },
];

export const RUBRIC_STYLES = [
  { value: 'italic', label: 'Italic', note: 'As in the 2019 Prayer Book' },
  { value: 'red', label: 'Red', note: 'As in older Prayer Books' },
];

const THEME_VALUES = THEMES.map((t) => t.value);
const RUBRIC_VALUES = RUBRIC_STYLES.map((r) => r.value);
const FONT_VALUES = READING_FONTS.map((f) => f.value);

export const displayState = reactive({
  theme: 'auto',
  resolvedTheme: 'light',
  fontSize: DEFAULT_FONT_SIZE,
  readingFont: 'caslon',
  rubricStyle: 'italic',
  audioEnabled: true,
  loaded: false,
});

let systemQuery = null;

function systemTheme() {
  if (typeof window === 'undefined' || !window.matchMedia) return 'light';
  return window.matchMedia('(prefers-color-scheme: dark)').matches
    ? 'dark'
    : 'light';
}

function root() {
  return typeof document === 'undefined' ? null : document.documentElement;
}

function updateThemeColorMeta() {
  if (typeof document === 'undefined' || !window.getComputedStyle) return;
  const paper = window
    .getComputedStyle(document.documentElement)
    .getPropertyValue('--paper')
    .trim();
  if (!paper) return;
  let meta = document.querySelector('meta[name="theme-color"]');
  if (!meta) {
    meta = document.createElement('meta');
    meta.setAttribute('name', 'theme-color');
    document.head.appendChild(meta);
  }
  meta.setAttribute('content', paper);
}

export function applyTheme() {
  const el = root();
  displayState.resolvedTheme =
    displayState.theme === 'auto' ? systemTheme() : displayState.theme;
  if (!el) return;
  el.classList.remove('light', 'sepia', 'dark');
  el.classList.add(displayState.resolvedTheme);
  refreshSeasonAccent();
  updateThemeColorMeta();
}

export function applyFontSize() {
  const el = root();
  if (!el) return;
  const size = displayState.fontSize;
  el.style.setProperty('--main-font-size', `${size}px`);
  el.style.setProperty('--main-line-height', `${Math.round(size * 1.55)}px`);
}

export function applyReadingFont() {
  const el = root();
  if (!el) return;
  if (displayState.readingFont === 'caslon') {
    delete el.dataset.readingFont;
  } else {
    el.dataset.readingFont = displayState.readingFont;
  }
}

export function applyRubricStyle() {
  const el = root();
  if (!el) return;
  if (displayState.rubricStyle === 'red') {
    el.dataset.rubrics = 'red';
  } else {
    delete el.dataset.rubrics;
  }
}

export function applyAll() {
  applyTheme();
  applyFontSize();
  applyReadingFont();
  applyRubricStyle();
}

function watchSystemTheme() {
  if (systemQuery || typeof window === 'undefined' || !window.matchMedia) {
    return;
  }
  systemQuery = window.matchMedia('(prefers-color-scheme: dark)');
  systemQuery.addEventListener?.('change', () => {
    if (displayState.theme === 'auto') applyTheme();
  });
}

function parseFontSize(raw) {
  const value = parseInt(raw, 10);
  if (Number.isNaN(value)) return DEFAULT_FONT_SIZE;
  return Math.min(48, Math.max(12, value));
}

export async function loadDisplayPreferences() {
  const [theme, fontSize, readingFont, rubricStyle, audioEnabled] =
    await Promise.all([
      DynamicStorage.getItem('user-theme'),
      DynamicStorage.getItem('fontSize'),
      DynamicStorage.getItem('readingFont'),
      DynamicStorage.getItem('rubricStyle'),
      DynamicStorage.getItem('audioEnabled'),
    ]);
  displayState.theme = THEME_VALUES.includes(theme) ? theme : 'auto';
  displayState.fontSize = parseFontSize(fontSize ?? DEFAULT_FONT_SIZE);
  displayState.readingFont = FONT_VALUES.includes(readingFont)
    ? readingFont
    : 'caslon';
  displayState.rubricStyle = RUBRIC_VALUES.includes(rubricStyle)
    ? rubricStyle
    : 'italic';
  displayState.audioEnabled = !(
    audioEnabled === 'false' || audioEnabled === false
  );
  displayState.loaded = true;
  watchSystemTheme();
  applyAll();
  return displayState;
}

export async function setTheme(theme) {
  if (!THEME_VALUES.includes(theme)) return;
  displayState.theme = theme;
  applyTheme();
  await DynamicStorage.setItem('user-theme', theme);
}

export async function setFontSize(size) {
  displayState.fontSize = parseFontSize(size);
  applyFontSize();
  await DynamicStorage.setItem('fontSize', String(displayState.fontSize));
}

/** Move one notch along FONT_SIZES (direction is +1 or -1). */
export function nextFontSize(current, direction) {
  if (direction > 0) {
    return FONT_SIZES.find((s) => s > current) ?? current;
  }
  return [...FONT_SIZES].reverse().find((s) => s < current) ?? current;
}

export async function stepFontSize(direction) {
  await setFontSize(nextFontSize(displayState.fontSize, direction));
}

export function fontSizePercent(size = displayState.fontSize) {
  return Math.round((size / DEFAULT_FONT_SIZE) * 100);
}

export async function setReadingFont(font) {
  if (!FONT_VALUES.includes(font)) return;
  displayState.readingFont = font;
  applyReadingFont();
  await DynamicStorage.setItem('readingFont', font);
}

export async function setRubricStyle(style) {
  if (!RUBRIC_VALUES.includes(style)) return;
  displayState.rubricStyle = style;
  applyRubricStyle();
  await DynamicStorage.setItem('rubricStyle', style);
}

export async function setAudioEnabled(enabled) {
  displayState.audioEnabled = Boolean(enabled);
  await DynamicStorage.setItem(
    'audioEnabled',
    displayState.audioEnabled ? 'true' : 'false'
  );
}

export async function resetDisplayPreferences() {
  await Promise.all([
    setTheme('auto'),
    setFontSize(DEFAULT_FONT_SIZE),
    setReadingFont('caslon'),
    setRubricStyle('italic'),
    setAudioEnabled(true),
  ]);
}

export function hasCustomDisplay() {
  return (
    displayState.theme !== 'auto' ||
    displayState.fontSize !== DEFAULT_FONT_SIZE ||
    displayState.readingFont !== 'caslon' ||
    displayState.rubricStyle !== 'italic' ||
    !displayState.audioEnabled
  );
}
