/*
  Discovery
  =========
  Quiet, one-time nudges that help people find the Display options without
  adding permanent clutter.

    - A dot on the header's Aa button until the Display panel has been
      opened, and once more whenever the panel gains a feature.
    - A "Make it yours" card at the end of the office until it's dismissed.

  When the Display panel gains a feature, bump DISPLAY_FEATURES_VERSION so
  the dot returns once for everyone.
*/
import { reactive } from 'vue';
import { DynamicStorage } from '@/helpers/storage';

// 1: theme, size, typeface, audio. 2: rubric style. 3: margin contents.
export const DISPLAY_FEATURES_VERSION = 3;

export const discoveryState = reactive({
  // Start "seen" so nothing flashes before storage is read.
  displayNew: false,
  showDisplayCard: false,
  loaded: false,
});

export async function loadDiscovery() {
  const [seenVersion, cardDismissed] = await Promise.all([
    DynamicStorage.getItem('displaySeenVersion'),
    DynamicStorage.getItem('displayCardDismissed'),
  ]);
  const seen = parseInt(seenVersion || '0', 10) || 0;
  discoveryState.displayNew = seen < DISPLAY_FEATURES_VERSION;
  discoveryState.showDisplayCard = cardDismissed !== 'true';
  discoveryState.loaded = true;
  return discoveryState;
}

export async function markDisplaySeen() {
  if (!discoveryState.displayNew) return;
  discoveryState.displayNew = false;
  await DynamicStorage.setItem(
    'displaySeenVersion',
    String(DISPLAY_FEATURES_VERSION)
  );
}

export async function dismissDisplayCard() {
  discoveryState.showDisplayCard = false;
  await DynamicStorage.setItem('displayCardDismissed', 'true');
}
