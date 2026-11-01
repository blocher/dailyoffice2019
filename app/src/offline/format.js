// Words for the Offline panel and notices.

export function formatBytes(bytes) {
  if (!bytes) return '0 MB';
  const mb = bytes / (1024 * 1024);
  if (mb < 0.1) return 'under 0.1 MB';
  if (mb < 10) return `${mb.toFixed(1)} MB`;
  if (mb < 1000) return `${Math.round(mb)} MB`;
  return `${(mb / 1024).toFixed(1)} GB`;
}

export function fromIso(iso) {
  const [year, month, day] = iso.split('-').map(Number);
  return new Date(year, month - 1, day);
}

// "today", "tomorrow", "Sunday", or "Sunday, November 30"
export function friendlyDate(iso, now = new Date()) {
  if (!iso) return '';
  const date = fromIso(iso);
  const today = new Date(now);
  today.setHours(0, 0, 0, 0);
  const days = Math.round((date - today) / 86400000);
  if (days === 0) return 'today';
  if (days === 1) return 'tomorrow';
  if (days > 1 && days < 7) {
    return date.toLocaleDateString('en-US', { weekday: 'long' });
  }
  return date.toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  });
}

export function relativeTime(ms, now = Date.now()) {
  if (!ms) return '';
  const seconds = Math.max(0, Math.round((now - ms) / 1000));
  if (seconds < 60) return 'just now';
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes} minute${minutes === 1 ? '' : 's'} ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} hour${hours === 1 ? '' : 's'} ago`;
  const days = Math.round(hours / 24);
  return `${days} day${days === 1 ? '' : 's'} ago`;
}

// Rough sizes, for choosing how many days to keep (measured from the API).
export const ESTIMATE_BYTES = {
  dailyOfficesPerDay: 420 * 1024,
  familyPerDay: 120 * 1024,
  readingsPerDay: 150 * 1024,
  calendarPerMonth: 1024 * 1024,
  library: 2 * 1024 * 1024,
  audioPerOffice: 26 * 1024 * 1024,
};

export function estimateBytes({ days, family, readings }) {
  if (!days) return 0;
  const perDay =
    ESTIMATE_BYTES.dailyOfficesPerDay +
    (family ? ESTIMATE_BYTES.familyPerDay : 0) +
    (readings ? ESTIMATE_BYTES.readingsPerDay : 0);
  const months = Math.ceil(days / 30) + 1;
  return (
    perDay * days +
    months * ESTIMATE_BYTES.calendarPerMonth +
    ESTIMATE_BYTES.library
  );
}
