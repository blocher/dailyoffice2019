<template>
  <nav class="day-line" aria-label="Choose a day">
    <router-link
      :to="prevTo"
      class="day-line__step"
      aria-label="Previous day"
      @click="toTop"
    >
      <UiIcon name="chevron-left" />
    </router-link>
    <div class="day-line__center">
      <router-link :to="calendarTo" class="day-line__date">
        {{ formattedDate }}
      </router-link>
      <router-link
        v-if="!isToday"
        :to="todayTo"
        class="day-line__today"
        @click="toTop"
      >
        Return to today
      </router-link>
    </div>
    <router-link
      :to="nextTo"
      class="day-line__step"
      aria-label="Next day"
      @click="toTop"
    >
      <UiIcon name="chevron-right" />
    </router-link>
  </nav>
</template>

<script setup>
import { computed } from 'vue';

/*
  ‹ Sunday, October 11, 2026 ›  — the date, with the days either side.
  Shared by the office and readings pages; each passes its own links so the
  kind of service is kept when moving between days.
*/
const props = defineProps({
  date: { type: Date, required: true },
  prevTo: { type: [String, Object], required: true },
  nextTo: { type: [String, Object], required: true },
  todayTo: { type: [String, Object], required: true },
  calendarTo: { type: [String, Object], required: true },
  isToday: { type: Boolean, default: false },
});

const formattedDate = computed(() =>
  props.date.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
);

function toTop() {
  window.scrollTo(0, 0);
}
</script>

<style scoped>
.day-line {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  width: 100%;
  max-width: 34rem;
  margin: var(--space-1) auto 0;
}

.day-line__step {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 2.75rem;
  height: 2.75rem;
  border-radius: 50%;
  color: var(--ink-soft);
  font-size: 1.15rem;
  text-decoration: none;
  transition: background-color var(--duration) var(--ease);
}

.day-line__step:hover {
  background-color: var(--paper-sunken);
  color: var(--ink);
}

.day-line__center {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  min-width: 0;
}

.day-line__date {
  font-size: var(--text-md);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.12em;
  color: var(--ink-soft);
  text-align: center;
  text-decoration: none;
}

.day-line__date:hover {
  color: var(--accent);
}

.day-line__today {
  font-size: var(--text-xs);
  font-style: italic;
}
</style>
