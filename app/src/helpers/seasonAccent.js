const ACCENT_MAP = {
  red: { token: '--season-red' },
  green: { token: '--season-green' },
  purple: { token: '--season-purple' },
  white: { token: '--season-white' },
  black: { token: '--season-black' },
  rose: { token: '--season-rose' },
  blue: { token: '--season-blue' },
};

const LIGHT_TEXT = '#ffffff';
const DARK_TEXT = '#0b1220';

export function normalizeLiturgicalColor(color) {
  if (!color || typeof color !== 'string') {
    return null;
  }
  return color.trim().toLowerCase();
}

export function resolveColorFromCard(card, office = null) {
  if (!card) {
    return null;
  }

  const isEveningOffice = ['evening_prayer', 'compline'].includes(office);
  const candidates = isEveningOffice
    ? [card.primary_evening_color, card.primary_color]
    : [card.primary_color, card.primary_evening_color];

  if (Array.isArray(card.colors) && card.colors.length) {
    candidates.push(card.colors[0]);
  }
  if (
    card.season &&
    Array.isArray(card.season.colors) &&
    card.season.colors.length
  ) {
    candidates.push(card.season.colors[0]);
  }
  if (
    Array.isArray(card.commemorations) &&
    card.commemorations.length &&
    Array.isArray(card.commemorations[0].colors) &&
    card.commemorations[0].colors.length
  ) {
    candidates.push(card.commemorations[0].colors[0]);
  }

  for (const candidate of candidates) {
    const normalized = normalizeLiturgicalColor(candidate);
    if (normalized && ACCENT_MAP[normalized]) {
      return normalized;
    }
  }
  return null;
}

export function setSeasonAccent(color) {
  if (typeof document === 'undefined' || typeof window === 'undefined') {
    return;
  }

  const normalized = normalizeLiturgicalColor(color);
  if (!normalized || !ACCENT_MAP[normalized]) {
    return;
  }

  const root = document.documentElement;
  const accent = ACCENT_MAP[normalized];
  const accentReference = `var(${accent.token})`;
  const contrast = getBestContrastColor(accentReference);
  root.dataset.seasonAccent = normalized;
  root.style.setProperty('--accent-key', normalized);
  root.style.setProperty('--accent-token', accent.token);
  root.style.setProperty('--accent-color', accentReference);
  root.style.setProperty('--accent-contrast', contrast);
}

export function refreshSeasonAccent() {
  if (typeof document === 'undefined') {
    return;
  }
  const storedAccent = document.documentElement.dataset.seasonAccent;
  if (storedAccent) {
    setSeasonAccent(storedAccent);
  }
}

function getBestContrastColor(accentColorReference) {
  const accentRgb = resolveCssColor(accentColorReference);
  if (!accentRgb) {
    return LIGHT_TEXT;
  }

  const lightRatio = contrastRatio(accentRgb, [255, 255, 255]);
  const darkRatio = contrastRatio(accentRgb, [11, 18, 32]);
  return lightRatio >= darkRatio ? LIGHT_TEXT : DARK_TEXT;
}

function resolveCssColor(cssColorReference) {
  const probe = document.createElement('span');
  probe.style.color = cssColorReference;
  probe.style.position = 'absolute';
  probe.style.visibility = 'hidden';
  probe.style.pointerEvents = 'none';
  document.body.appendChild(probe);
  const computedColor = window.getComputedStyle(probe).color;
  probe.remove();

  const match = computedColor.match(/^rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/);
  if (!match) {
    return null;
  }
  return [
    parseInt(match[1], 10),
    parseInt(match[2], 10),
    parseInt(match[3], 10),
  ];
}

function contrastRatio(a, b) {
  const aLuminance = relativeLuminance(a);
  const bLuminance = relativeLuminance(b);
  const lighter = Math.max(aLuminance, bLuminance);
  const darker = Math.min(aLuminance, bLuminance);
  return (lighter + 0.05) / (darker + 0.05);
}

function relativeLuminance([r, g, b]) {
  const [red, green, blue] = [r, g, b].map((channel) => {
    const normalized = channel / 255;
    return normalized <= 0.03928
      ? normalized / 12.92
      : Math.pow((normalized + 0.055) / 1.055, 2.4);
  });

  return 0.2126 * red + 0.7152 * green + 0.0722 * blue;
}
