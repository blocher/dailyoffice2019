<template>
  <section class="offline-miss" aria-labelledby="offline-miss-title">
    <span class="offline-miss__icon" aria-hidden="true">
      <UiIcon name="cloud-off" />
    </span>
    <h2 id="offline-miss-title" class="offline-miss__title">
      Not downloaded yet
    </h2>
    <p class="offline-miss__text">{{ message }}</p>
    <div class="offline-miss__actions">
      <UiButton v-if="todayLink" variant="primary" icon="book" :to="todayLink">
        {{ todayLabel }}
      </UiButton>
      <UiButton icon="cloud-download" @click="openPanel('offline')">
        What’s downloaded
      </UiButton>
    </div>
  </section>
</template>

<script setup>
/*
  Shown in place of an office (or another page) that isn't on the device
  while offline: says why, and offers today's office instead.
*/
import { computed } from 'vue';
import { openPanel } from '@/helpers/panels';
import { effectiveDays, syncState } from '@/offline';
import { friendlyDate } from '@/offline/format';

const props = defineProps({
  what: { type: String, default: 'office' },
  date: { type: Date, default: null },
  office: { type: String, default: '' },
  serviceType: { type: String, default: 'office' },
});

const NAMES = {
  morning_prayer: 'Morning Prayer',
  midday_prayer: 'Midday Prayer',
  evening_prayer: 'Evening Prayer',
  compline: 'Compline',
  early_evening_prayer: 'Early Evening Prayer',
  close_of_day_prayer: 'Prayer at the Close of Day',
};

function startOfToday() {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return today;
}

const offsetDays = computed(() =>
  props.date ? Math.round((props.date - startOfToday()) / 86400000) : 0
);

const isToday = computed(() => offsetDays.value === 0);

const message = computed(() => {
  const days = effectiveDays();
  const name = NAMES[props.office] || 'This office';
  const when = props.date
    ? props.date.toLocaleDateString('en-US', {
        weekday: 'long',
        month: 'long',
        day: 'numeric',
      })
    : '';
  if (days === 0) {
    return `You’re offline, and downloads are off. Turn them on in Offline to keep the days ahead on this device.`;
  }
  if (offsetDays.value < -1) {
    return `You’re offline. ${name} for ${when} has passed, and past days aren’t kept.`;
  }
  if (offsetDays.value >= days) {
    return `You’re offline. This device keeps ${days} days ahead, and ${when} is further out.`;
  }
  if (syncState.readyThrough) {
    return `You’re offline, and ${name} for ${when} hadn’t finished downloading. Offices are ready through ${friendlyDate(syncState.readyThrough)}.`;
  }
  return `You’re offline, and ${name} for ${when} hadn’t downloaded yet. It will the next time you’re online.`;
});

const todayLink = computed(() => {
  if (isToday.value || !syncState.readyThrough) return null;
  if (props.serviceType === 'family') return `/family/${props.office}`;
  return props.office ? `/office/${props.office}` : '/';
});

const todayLabel = computed(() =>
  props.office ? `Today’s ${NAMES[props.office]}` : 'Pray today'
);
</script>

<style scoped>
.offline-miss {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
  max-width: 30rem;
  margin: var(--space-4) auto var(--space-6);
  padding: var(--space-6) var(--space-5);
  border: 1px solid var(--rule);
  border-radius: var(--radius-lg);
  background-color: var(--paper-raised);
  text-align: center;
}

.offline-miss__icon {
  display: grid;
  place-items: center;
  width: 3rem;
  height: 3rem;
  border-radius: 50%;
  background-color: var(--paper-sunken);
  color: var(--accent);
  font-size: 1.4rem;
}

.offline-miss__title {
  font-size: var(--text-lg);
  font-weight: 400;
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
}

.offline-miss__text {
  font-size: var(--text-md);
  font-style: italic;
  color: var(--ink-soft);
  line-height: var(--leading-prose);
}

.offline-miss__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--space-2);
  margin-top: var(--space-2);
}
</style>
