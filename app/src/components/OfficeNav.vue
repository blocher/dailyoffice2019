<template>
  <nav class="office-nav" aria-label="Choose an office">
    <UiSegmented
      class="office-nav__mode"
      :model-value="currentServiceType"
      :options="modeOptions"
      size="sm"
      aria-label="Kind of prayer"
      @update:model-value="setServiceType"
    />

    <ul class="office-tabs">
      <li v-for="link in links" :key="link.name">
        <router-link
          :to="link.to"
          class="office-tab"
          :class="{ 'is-active': selectedOffice === link.name }"
          :aria-current="selectedOffice === link.name ? 'page' : null"
        >
          <UiIcon :name="link.icon" class="office-tab__icon" />
          <span class="office-tab__label">{{ link.text }}</span>
        </router-link>
      </li>
    </ul>

    <DayLine
      v-if="showDayLine"
      :date="calendarDate"
      :prev-to="dayLinks[0]?.to || ''"
      :next-to="dayLinks[2]?.to || ''"
      :today-to="todayLink"
      :calendar-to="calendarLink"
      :is-today="isViewingToday"
    />
  </nav>
</template>

<script>
import DayLine from '@/components/DayLine.vue';
import { DynamicStorage } from '@/helpers/storage';

const DAILY = [
  { name: 'morning_prayer', text: 'Morning', icon: 'sunrise' },
  { name: 'midday_prayer', text: 'Midday', icon: 'sun' },
  { name: 'evening_prayer', text: 'Evening', icon: 'sunset' },
  { name: 'compline', text: 'Compline', icon: 'moon' },
];

const FAMILY = [
  { name: 'morning_prayer', text: 'Morning', icon: 'sunrise' },
  { name: 'midday_prayer', text: 'Midday', icon: 'sun' },
  { name: 'early_evening_prayer', text: 'Early Evening', icon: 'sunset' },
  { name: 'close_of_day_prayer', text: 'Close of Day', icon: 'moon' },
];

const TO_FAMILY = {
  morning_prayer: 'morning_prayer',
  midday_prayer: 'midday_prayer',
  evening_prayer: 'early_evening_prayer',
  compline: 'close_of_day_prayer',
};

const TO_DAILY = {
  morning_prayer: 'morning_prayer',
  midday_prayer: 'midday_prayer',
  early_evening_prayer: 'evening_prayer',
  close_of_day_prayer: 'compline',
};

function datePath(date) {
  return `${date.getFullYear()}/${date.getMonth() + 1}/${date.getDate()}`;
}

export default {
  name: 'OfficeNav',
  components: { DayLine },
  props: {
    calendarDate: {
      type: Date,
    },
    selectedOffice: {
      type: String,
    },
    serviceType: {
      default: 'office',
      type: String,
    },
    // The Day page shows its own date, so it hides this.
    showDayLine: {
      default: true,
      type: Boolean,
    },
  },
  data() {
    return {
      links: [],
      dailyLinks: [],
      familyLinks: [],
      dayLinks: [],
      currentServiceType: this.serviceType,
      modeOptions: [
        { value: 'office', label: 'Daily Office' },
        { value: 'family', label: 'Family Prayer' },
      ],
    };
  },
  computed: {
    isViewingToday() {
      const today = new Date();
      return (
        this.calendarDate.getFullYear() === today.getFullYear() &&
        this.calendarDate.getMonth() === today.getMonth() &&
        this.calendarDate.getDate() === today.getDate()
      );
    },
    todayLink() {
      const today = new Date();
      const servicePart = this.currentServiceType === 'family' ? '/family' : '';
      return `${servicePart}/${this.selectedOffice}/${today.getFullYear()}/${
        today.getMonth() + 1
      }/${today.getDate()}`;
    },
    calendarLink() {
      return `/calendar/${this.calendarDate.getFullYear()}/${
        this.calendarDate.getMonth() + 1
      }/`;
    },
  },
  async created() {
    const tomorrow = new Date(this.calendarDate);
    tomorrow.setDate(this.calendarDate.getDate() + 1);
    const yesterday = new Date(this.calendarDate);
    yesterday.setDate(this.calendarDate.getDate() - 1);
    const today = datePath(this.calendarDate);

    this.dailyLinks = DAILY.map((link) => ({
      ...link,
      to: `/${link.name}/${today}`,
    }));
    this.familyLinks = FAMILY.map((link) => ({
      ...link,
      to: `/family/${link.name}/${today}`,
    }));
    this.links =
      this.currentServiceType === 'family' ? this.familyLinks : this.dailyLinks;

    const servicePart =
      this.currentServiceType === 'family' ? `/${this.currentServiceType}` : '';
    this.dayLinks = [
      {
        to: `${servicePart}/${this.selectedOffice}/${datePath(yesterday)}`,
        text: 'Previous',
        icon: 'left',
        selected: false,
      },
      {
        to: `${servicePart}/${this.selectedOffice}/${today}`,
        text: 'Selected day',
        icon: '',
        selected: true,
      },
      {
        to: `${servicePart}/${this.selectedOffice}/${datePath(tomorrow)}`,
        text: 'Next',
        icon: 'right',
        selected: false,
      },
    ];
  },
  methods: {
    async setServiceType(type) {
      if (type === this.currentServiceType) return;
      const lookup = type === 'family' ? TO_FAMILY : TO_DAILY;
      const office = lookup[this.selectedOffice];
      this.currentServiceType = type;
      this.links = type === 'family' ? this.familyLinks : this.dailyLinks;
      await DynamicStorage.setItem('serviceType', type);
      if (!office) return;
      const prefix = type === 'family' ? '/family' : '';
      this.$router.push(`${prefix}/${office}/${datePath(this.calendarDate)}`);
    },
  },
};
</script>

<style scoped>
.office-nav {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
}

/* Office tabs */
.office-tabs {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  width: 100%;
  max-width: 34rem;
  border-bottom: 1px solid var(--rule);
}

.office-tab {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.2rem;
  min-height: 3.5rem;
  padding: var(--space-2) var(--space-1);
  color: var(--ink-soft);
  font-size: var(--text-sm);
  line-height: 1.15;
  text-align: center;
  text-decoration: none;
  transition: color var(--duration) var(--ease);
}

.office-tab::after {
  content: '';
  position: absolute;
  left: 18%;
  right: 18%;
  bottom: -1px;
  height: 2px;
  border-radius: 2px;
  background-color: transparent;
  transition: background-color var(--duration) var(--ease);
}

.office-tab:hover {
  color: var(--ink);
}

.office-tab.is-active {
  color: var(--ink);
}

.office-tab.is-active::after {
  background-color: var(--accent);
}

.office-tab__icon {
  font-size: 1.2rem;
  color: var(--ink-faint);
  transition: color var(--duration) var(--ease);
}

.office-tab.is-active .office-tab__icon {
  color: var(--accent);
}

@media (min-width: 560px) {
  .office-tab {
    flex-direction: row;
    gap: 0.45rem;
    font-size: var(--text-md);
  }
}
</style>
