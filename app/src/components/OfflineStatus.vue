<template>
  <Transition name="offline-status">
    <button
      v-if="mode"
      type="button"
      class="header-action offline-status"
      :class="[`is-${mode}`, { 'is-open': panels.offline }]"
      :aria-label="label"
      :aria-expanded="panels.offline ? 'true' : 'false'"
      @click="toggle"
    >
      <span
        v-if="mode === 'syncing'"
        class="offline-status__ring"
        aria-hidden="true"
      >
        <svg viewBox="0 0 20 20" width="1em" height="1em">
          <circle cx="10" cy="10" r="8" class="offline-status__track" />
          <circle
            cx="10"
            cy="10"
            r="8"
            class="offline-status__value"
            :style="{ strokeDashoffset: dashOffset }"
          />
        </svg>
      </span>
      <UiIcon v-else name="cloud-off" class="offline-status__icon" />
      <span class="offline-status__label">{{ shortLabel }}</span>
    </button>
  </Transition>
</template>

<script setup>
/*
  A quiet sign in the header, only when it matters: while offline, and while
  the days ahead download for new settings (or for the first time). Opens
  the Offline panel.
*/
import { computed } from 'vue';
import { network, syncState } from '@/offline';
import { openPanel, panels } from '@/helpers/panels';

const CIRCUMFERENCE = 2 * Math.PI * 8;

const mode = computed(() => {
  if (!network.online) return 'offline';
  if (
    syncState.status === 'syncing' &&
    syncState.total > 3 &&
    (syncState.reason === 'settings' || syncState.readyDays === 0)
  ) {
    return 'syncing';
  }
  return null;
});

const dashOffset = computed(() => {
  const share = syncState.total ? syncState.done / syncState.total : 0;
  return CIRCUMFERENCE * (1 - share);
});

const shortLabel = computed(() =>
  mode.value === 'offline' ? 'Offline' : 'Downloading'
);

const label = computed(() =>
  mode.value === 'offline'
    ? 'Offline. Show what’s downloaded'
    : `Downloading for offline use, ${syncState.done} of ${syncState.total}`
);

function toggle() {
  if (panels.offline) panels.offline = false;
  else openPanel('offline');
}
</script>

<style scoped>
.offline-status {
  color: var(--ink-soft);
}

.offline-status.is-offline {
  color: var(--ink);
  background-color: var(--paper-sunken);
}

.offline-status.is-offline .offline-status__icon {
  color: var(--accent);
}

.offline-status__label {
  display: none;
}

/* No room for the download ring on the smallest phones; the Offline panel
   and the menu still show the progress. */
@media (max-width: 399px) {
  .offline-status.is-syncing {
    display: none;
  }
}

@media (min-width: 480px) {
  .offline-status.is-offline .offline-status__label {
    display: inline;
  }
}

@media (min-width: 860px) {
  .offline-status__label {
    display: inline;
  }
}

/* As AppHeader's .header-action__icon, whose scoped style can't reach in
   here (only this component's root). */
.offline-status__icon {
  position: relative;
  top: -0.09em;
  font-size: 1.1rem;
}

.offline-status__ring {
  display: inline-grid;
  place-items: center;
  font-size: 1.1rem;
}

.offline-status__ring svg {
  transform: rotate(-90deg);
}

.offline-status__track,
.offline-status__value {
  fill: none;
  stroke-width: 2.25;
}

.offline-status__track {
  stroke: var(--rule-strong);
}

.offline-status__value {
  stroke: var(--accent);
  stroke-linecap: round;
  stroke-dasharray: 50.27;
  transition: stroke-dashoffset 300ms var(--ease);
}

.offline-status-enter-active,
.offline-status-leave-active {
  transition:
    opacity 200ms var(--ease),
    transform 200ms var(--ease);
}

.offline-status-enter-from,
.offline-status-leave-to {
  opacity: 0;
  transform: scale(0.9);
}
</style>
