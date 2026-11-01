/*
  What's New
  ==========
  Feature announcements come with the site messages (kind "whats_new").
  Instead of a banner each, they share one "What's new" banner that counts
  them and opens a sheet listing them all; the menu opens the sheet too.

  Looking doesn't dismiss anything. Each entry is dismissed on its own (or
  by following its link), or all at once from the banner or the sheet, and
  the banner returns only when a new entry is added. Dismissed entries stay
  in the sheet under "Earlier".

  Before the sheet, every announcement was its own banner, dismissed into
  'dismissedSiteMessages'. An entry whose old banner was dismissed counts as
  dismissed, so turning an announcement into an entry doesn't show it again.
*/
import { computed, reactive } from 'vue';
import { addToStoredList, readStoredList } from '@/helpers/storedList';

const DISMISSED_KEY = 'dismissedWhatsNew';
const DISMISSED_BANNERS_KEY = 'dismissedSiteMessages';

export const whatsNewState = reactive({
  entries: [],
  dismissed: [],
  // Until the site messages arrive, the sheet (opened from a link, say)
  // shows that it's loading rather than "nothing new".
  status: 'loading', // loading | ready | failed
});

function readDismissed() {
  return [
    ...readStoredList('localStorage', DISMISSED_KEY),
    ...readStoredList('localStorage', DISMISSED_BANNERS_KEY),
  ];
}

export function setWhatsNew(entries, { failed = false } = {}) {
  whatsNewState.dismissed = readDismissed();
  whatsNewState.entries = entries;
  whatsNewState.status = failed && !entries.length ? 'failed' : 'ready';
}

export const newWhatsNew = computed(() =>
  whatsNewState.entries.filter(
    (entry) => !whatsNewState.dismissed.includes(entry.uuid)
  )
);

export const earlierWhatsNew = computed(() =>
  whatsNewState.entries.filter((entry) =>
    whatsNewState.dismissed.includes(entry.uuid)
  )
);

function dismiss(ids) {
  whatsNewState.dismissed = [...new Set([...whatsNewState.dismissed, ...ids])];
  addToStoredList('localStorage', DISMISSED_KEY, ids);
}

export function dismissWhatsNew(entry) {
  dismiss([entry.uuid]);
}

export function dismissAllWhatsNew() {
  dismiss(newWhatsNew.value.map((entry) => entry.uuid));
}

// "Offline mode", "Offline mode and Book view",
// "Offline mode, Book view, and 2 more"
export function summarizeTitles(entries) {
  const titles = entries.map((entry) => entry.title || entry.text);
  if (titles.length <= 2) return titles.join(' and ');
  return `${titles[0]}, ${titles[1]}, and ${titles.length - 2} more`;
}
