<template>
  <nav class="office-continue" aria-label="Previous and next office">
    <router-link :to="previous.to" class="office-continue__link" @click="top">
      <span class="office-continue__dir">
        <UiIcon name="arrow-left" /> Previous
      </span>
      <span class="office-continue__name">{{ previous.label }}</span>
    </router-link>
    <router-link
      :to="next.to"
      class="office-continue__link office-continue__link--next"
      @click="top"
    >
      <span class="office-continue__dir">
        Next <UiIcon name="arrow-right" />
      </span>
      <span class="office-continue__name">{{ next.label }}</span>
    </router-link>
  </nav>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  office: { type: String, required: true },
  calendarDate: { type: Date, required: true },
  serviceType: { type: String, default: 'office' },
});

const SEQUENCES = {
  office: [
    ['morning_prayer', 'Morning Prayer'],
    ['midday_prayer', 'Midday Prayer'],
    ['evening_prayer', 'Evening Prayer'],
    ['compline', 'Compline'],
  ],
  family: [
    ['morning_prayer', 'Morning'],
    ['midday_prayer', 'Midday'],
    ['early_evening_prayer', 'Early Evening'],
    ['close_of_day_prayer', 'Close of Day'],
  ],
};

function shift(date, days) {
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return result;
}

function build(index, dayOffset) {
  const sequence = SEQUENCES[props.serviceType] || SEQUENCES.office;
  const [name, label] = sequence[index];
  const date = shift(props.calendarDate, dayOffset);
  const prefix = props.serviceType === 'family' ? '/family' : '';
  const sameDay = dayOffset === 0;
  const weekday = date.toLocaleDateString('en-US', { weekday: 'long' });
  return {
    to: `${prefix}/${name}/${date.getFullYear()}/${date.getMonth() + 1}/${date.getDate()}`,
    label: sameDay ? label : `${label}, ${weekday}`,
  };
}

const position = computed(() => {
  const sequence = SEQUENCES[props.serviceType] || SEQUENCES.office;
  return Math.max(
    0,
    sequence.findIndex(([name]) => name === props.office)
  );
});

const previous = computed(() =>
  position.value === 0 ? build(3, -1) : build(position.value - 1, 0)
);

const next = computed(() =>
  position.value === 3 ? build(0, 1) : build(position.value + 1, 0)
);

function top() {
  window.scrollTo(0, 0);
}
</script>

<style scoped>
.office-continue {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3);
  max-width: 40rem;
  margin: 0 auto;
  padding: 0 var(--gutter);
}

.office-continue__link {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--rule);
  border-radius: var(--radius-lg);
  background-color: var(--paper-raised);
  color: var(--ink);
  text-decoration: none;
  transition: border-color var(--duration) var(--ease);
}

.office-continue__link:hover {
  border-color: var(--accent-rule);
}

.office-continue__link--next {
  align-items: flex-end;
  text-align: right;
}

.office-continue__dir {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: var(--text-sm);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
  color: var(--ink-faint);
}

.office-continue__name {
  font-size: var(--text-md);
  line-height: 1.25;
}
</style>
