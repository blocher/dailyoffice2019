<template>
  <header class="office-title">
    <h1 v-if="officeName" class="office-title__name">
      <Ornament glyph="[" class="office-title__flourish" />&#8202;{{
        officeName
      }}&#8202;<Ornament glyph="]" class="office-title__flourish" />
    </h1>

    <p v-if="feast" class="office-title__feast">
      <span
        class="swatch office-title__swatch"
        :class="`swatch--${color}`"
        :title="`Liturgical color: ${color}`"
      />
      <span v-html="feast" />
    </p>
    <p
      v-if="card && card.fast && card.fast.fast_day"
      class="office-title__fast"
    >
      <UiTag>Fast day</UiTag>
    </p>

    <ul v-if="commemorations.length" class="office-title__commemorations">
      <li v-for="commemoration in commemorations" :key="commemoration.name">
        <Commemoration :commemoration="commemoration" />
      </li>
    </ul>
  </header>
</template>

<script>
import Commemoration from '@/components/Commemoration.vue';

const DAILY_OFFICES = {
  morning_prayer: 'Daily Morning Prayer',
  midday_prayer: 'Daily Midday Prayer',
  evening_prayer: 'Daily Evening Prayer',
  compline: 'Compline',
};

const FAMILY_OFFICES = {
  morning_prayer: 'Family Prayer in the Morning',
  midday_prayer: 'Family Prayer at Midday',
  early_evening_prayer: 'Family Prayer in the Early Evening',
  close_of_day_prayer: 'Family Prayer at the Close of Day',
};

function plainText(html) {
  return String(html || '')
    .replace(/<[^>]*>/g, '')
    .replace(/\s+/g, ' ')
    .trim()
    .toLowerCase();
}

export default {
  name: 'CalendarCard',
  components: { Commemoration },
  props: ['card', 'calendarDate', 'office', 'serviceType'],
  computed: {
    isEvening() {
      return this.office === 'evening_prayer' || this.office === 'compline';
    },
    officeName() {
      if (this.serviceType === 'readings') return 'Readings';
      const offices =
        this.serviceType === 'family' ? FAMILY_OFFICES : DAILY_OFFICES;
      return offices[this.office] || null;
    },
    feast() {
      if (!this.card) return '';
      return this.isEvening
        ? this.card.primary_evening_feast
        : this.card.primary_feast;
    },
    color() {
      if (!this.card) return 'green';
      const value = this.isEvening
        ? this.card.primary_evening_color
        : this.card.primary_color;
      return (value || 'green').toLowerCase();
    },
    // Other observances of the day, skipping the one already named as the
    // day's feast.
    commemorations() {
      if (!this.card) return [];
      const list = this.isEvening
        ? this.card.evening_commemorations
        : this.card.commemorations;
      if (!Array.isArray(list) || list.length < 2) return [];
      const feast = plainText(this.feast);
      return list.filter((c) => plainText(c.name) !== feast);
    },
  },
};
</script>

<style scoped>
/* Sizes follow the reader's text size, so the day's information grows and
   shrinks with the prayers. */
.office-title {
  font-size: max(15px, calc(var(--main-font-size) * 0.75));
  text-align: center;
}

.office-title__name {
  font-size: 1.55em;
  font-weight: 400;
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
  line-height: 1.15;
  color: var(--ink);
  text-wrap: balance;
}

.office-title__flourish {
  display: inline-block;
  margin: 0 0.25em;
  font-size: 0.8em;
  vertical-align: 0.05em;
}

@media (max-width: 399px) {
  .office-title__flourish {
    display: none;
  }
}

@media (max-width: 559px) {
  .office-title {
    font-size: max(15px, calc(var(--main-font-size) * 0.68));
  }

  .office-title__name {
    font-size: 1.45em;
  }
}

.office-title__feast {
  margin: 0.55em auto 0;
  max-width: 30em;
  font-size: 1.12em;
  font-style: italic;
  line-height: 1.35;
  color: var(--ink-soft);
  text-wrap: balance;
}

.office-title__swatch {
  margin-right: 0.45em;
  vertical-align: 0.08em;
}

.office-title__fast {
  margin-top: 0.5em;
}

.office-title__commemorations {
  display: flex;
  flex-direction: column;
  gap: 0.9em;
  max-width: 32em;
  margin: 1.1em auto 0;
  padding-top: 1em;
  border-top: 1px solid var(--rule);
  text-align: left;
}
</style>
