<template>
  <div class="page page--wide calendar-page">
    <header class="page-header">
      <p class="eyebrow">The Christian Year</p>
      <h1 class="page-title">Calendar</h1>
      <p v-if="seasonNames" class="page-lede">{{ seasonNames }}</p>
    </header>

    <div class="calendar-toolbar">
      <div class="month-nav">
        <UiButton
          variant="ghost"
          size="lg"
          icon="chevron-left"
          class="month-nav__step"
          aria-label="Previous month"
          @click="selectDate('prev-month')"
        />
        <h2 class="month-nav__title" aria-live="polite">{{ monthLabel }}</h2>
        <UiButton
          variant="ghost"
          size="lg"
          icon="chevron-right"
          class="month-nav__step"
          aria-label="Next month"
          @click="selectDate('next-month')"
        />
      </div>
      <UiSegmented
        class="calendar-toolbar__filter"
        :model-value="includeMinorFeasts"
        :options="feastOptions"
        aria-label="Feasts to show"
        @update:model-value="setIncludeMinorFeasts"
      />
      <UiButton
        class="calendar-toolbar__today"
        variant="secondary"
        icon="calendar-days"
        @click="selectDate('today')"
      >
        Today
      </UiButton>
    </div>

    <UiAlert v-if="error" tone="error" :title="error" class="calendar-error" />
    <Loading v-if="loading" />

    <div v-if="!loading" class="calendar-layout">
      <div
        class="month"
        role="grid"
        :aria-label="monthLabel"
        @keydown="onGridKeydown"
      >
        <div class="month__row month__weekdays" role="row">
          <span
            v-for="weekday in weekdays"
            :key="weekday.long"
            class="month__weekday"
            role="columnheader"
            :aria-label="weekday.long"
          >
            <span class="weekday--long" aria-hidden="true">{{
              weekday.short
            }}</span>
            <span class="weekday--narrow" aria-hidden="true">{{
              weekday.narrow
            }}</span>
          </span>
        </div>
        <div
          v-for="(week, index) in weeks"
          :key="index"
          class="month__row"
          role="row"
        >
          <div
            v-for="(cell, cellIndex) in week"
            :key="cell ? cell.key : `blank-${index}-${cellIndex}`"
            class="month__cell"
            role="gridcell"
            :aria-selected="cell ? String(cell.key === selectedKey) : null"
          >
            <button
              v-if="cell"
              type="button"
              class="day"
              :class="[
                `day--${cell.color || 'none'}`,
                {
                  'is-today': cell.isToday,
                  'is-selected': cell.key === selectedKey,
                  'has-feast': cell.feast,
                  'is-major': cell.isMajor,
                },
              ]"
              :data-day="cell.key"
              :tabindex="cell.key === focusKey ? 0 : -1"
              :aria-current="cell.isToday ? 'date' : null"
              :aria-label="cell.label"
              @click="clickDateCell(cell, $event)"
            >
              <span class="day__head">
                <span class="day__number">{{ cell.dayNumber }}</span>
                <span
                  v-if="cell.color"
                  class="swatch day__swatch"
                  :class="`swatch--${cell.color}`"
                  aria-hidden="true"
                />
              </span>
              <span
                v-if="cell.feast"
                class="day__feast"
                aria-hidden="true"
                v-html="cell.feast"
              />
            </button>
          </div>
        </div>
      </div>

      <section
        v-if="selectedDay"
        class="day-detail"
        aria-live="polite"
        aria-label="Selected day"
      >
        <p class="day-detail__date">
          <span>{{ selectedDateLabel }}</span>
          <UiTag v-if="selectedIsToday" tone="accent">Today</UiTag>
          <UiTag v-if="selectedDay.fast && selectedDay.fast.fast_day"
            >Fast day</UiTag
          >
        </p>
        <h2 class="day-detail__feast">
          <span
            class="swatch day-detail__swatch"
            :class="`swatch--${selectedColor}`"
            :title="`Liturgical color: ${selectedColor}`"
          />
          <span v-html="selectedDay.primary_feast" />
        </h2>
        <p v-if="selectedDay.season" class="day-detail__season">
          {{ selectedDay.season.name }}
        </p>

        <ul v-if="selectedCommemorations.length" class="day-detail__also">
          <li
            v-for="commemoration in selectedCommemorations"
            :key="commemoration.uuid || commemoration.name"
          >
            <span
              class="swatch day-detail__swatch day-detail__swatch--small"
              :class="`swatch--${colorOf(commemoration)}`"
              aria-hidden="true"
            />
            <router-link
              v-if="commemoration.uuid"
              :to="`/commemorations/${commemoration.uuid}`"
              ><span v-html="commemoration.name"
            /></router-link>
            <span v-else v-html="commemoration.name" />
          </li>
        </ul>

        <nav class="day-detail__pray" aria-label="Pray this day">
          <p class="day-detail__label">Pray</p>
          <ul class="day-links">
            <li v-for="link in selectedLinks" :key="link.to">
              <router-link :to="link.to" class="day-link">
                <UiIcon :name="link.icon" class="day-link__icon" />
                <span>{{ link.text }}</span>
              </router-link>
            </li>
          </ul>
          <router-link :to="selectedDayRoute" class="day-detail__more">
            The whole day&nbsp;›
          </router-link>
        </nav>
      </section>
    </div>

    <div class="divider" aria-hidden="true"><Ornament glyph="o" /></div>

    <section class="subscribe">
      <h2 class="section-title">In your calendar app</h2>
      <p class="subscribe__text">
        Add these feasts and readings to Apple Calendar, Google Calendar,
        Outlook, or any app that accepts a calendar address. A subscription
        keeps itself up to date.
      </p>
      <CalendarSubscriptionWizard
        ref="calendarSubscriptionWizard"
        :default-scope="calendarWizardDefaultScope"
        :include-minor-feasts="includeMinorFeasts"
      />
    </section>
  </div>
</template>

<script>
import CalendarSubscriptionWizard from '@/components/CalendarSubscriptionWizard.vue';
import Loading from '@/components/Loading.vue';
import { getCalendarWizardDefaultScope } from '@/helpers/calendarSubscription';
import { DynamicStorage } from '@/helpers/storage';

// 'all' (the default) or 'major'.
const FEAST_FILTER_KEY = 'calendarFeastFilter';

const WEEKDAYS = [
  { long: 'Sunday', short: 'Sun', narrow: 'S' },
  { long: 'Monday', short: 'Mon', narrow: 'M' },
  { long: 'Tuesday', short: 'Tue', narrow: 'T' },
  { long: 'Wednesday', short: 'Wed', narrow: 'W' },
  { long: 'Thursday', short: 'Thu', narrow: 'T' },
  { long: 'Friday', short: 'Fri', narrow: 'F' },
  { long: 'Saturday', short: 'Sat', narrow: 'S' },
];

const DAILY_OFFICES = [
  { name: 'morning_prayer', text: 'Morning', icon: 'sunrise' },
  { name: 'midday_prayer', text: 'Midday', icon: 'sun' },
  { name: 'evening_prayer', text: 'Evening', icon: 'sunset' },
  { name: 'compline', text: 'Compline', icon: 'moon' },
];

const FAMILY_OFFICES = [
  { name: 'morning_prayer', text: 'Morning', icon: 'sunrise' },
  { name: 'midday_prayer', text: 'Midday', icon: 'sun' },
  { name: 'early_evening_prayer', text: 'Early Evening', icon: 'sunset' },
  { name: 'close_of_day_prayer', text: 'Close of Day', icon: 'moon' },
];

const LITURGICAL_COLORS = [
  'red',
  'green',
  'purple',
  'white',
  'black',
  'rose',
  'blue',
];

function pad(value) {
  return String(value).padStart(2, '0');
}

function dateKey(year, month, day) {
  return `${year}-${pad(month)}-${pad(day)}`;
}

function plainText(html) {
  return String(html || '')
    .replace(/<[^>]*>/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

function normalizeColor(color) {
  const value = String(color || '').toLowerCase();
  return LITURGICAL_COLORS.includes(value) ? value : '';
}

export default {
  name: 'Calendar',
  components: {
    CalendarSubscriptionWizard,
    Loading,
  },
  data() {
    return {
      year: null,
      month: null,
      days: {},
      date: null,
      loading: true,
      error: false,
      includeMinorFeasts: true,
      selectedKey: null,
      pendingSubscriptionPanel: null,
      serviceType: 'office',
      weekdays: WEEKDAYS,
      feastOptions: [
        { value: false, label: 'Major feasts' },
        { value: true, label: 'All feasts' },
      ],
    };
  },
  computed: {
    calendarWizardDefaultScope() {
      return getCalendarWizardDefaultScope({
        source: 'calendar',
        includeMinorFeasts: this.includeMinorFeasts,
      });
    },
    monthLabel() {
      if (!this.year || !this.month) return 'Calendar';
      return new Date(this.year, this.month - 1, 1).toLocaleDateString(
        'en-US',
        { month: 'long', year: 'numeric' }
      );
    },
    todayKey() {
      const today = new Date();
      return dateKey(
        today.getFullYear(),
        today.getMonth() + 1,
        today.getDate()
      );
    },
    seasonNames() {
      const names = [];
      Object.values(this.days).forEach((day) => {
        const name = day?.season?.name;
        if (name && !names.includes(name)) names.push(name);
      });
      return names.join(' · ');
    },
    // The month as weeks of seven cells (null pads the first and last week).
    weeks() {
      if (!this.year || !this.month) return [];
      const leading = new Date(this.year, this.month - 1, 1).getDay();
      const count = new Date(this.year, this.month, 0).getDate();
      const monthName = new Date(this.year, this.month - 1, 1).toLocaleString(
        'en-US',
        { month: 'long' }
      );
      const cells = Array.from({ length: leading }, () => null);
      for (let dayNumber = 1; dayNumber <= count; dayNumber += 1) {
        const key = dateKey(this.year, this.month, dayNumber);
        const weekday = WEEKDAYS[(leading + dayNumber - 1) % 7].long;
        const feast = this.getFeastNameForDate(key);
        const color = normalizeColor(this.getColorForDate(key));
        const labelParts = [`${weekday}, ${monthName} ${dayNumber}`];
        if (feast) labelParts.push(plainText(feast));
        if (key === this.todayKey) labelParts.push('today');
        cells.push({
          key,
          dayNumber,
          feast,
          color,
          isMajor: Boolean(this.days[key]?.major_feast),
          isToday: key === this.todayKey,
          label: labelParts.join(', '),
        });
      }
      while (cells.length % 7) cells.push(null);
      const weeks = [];
      for (let i = 0; i < cells.length; i += 7) {
        weeks.push(cells.slice(i, i + 7));
      }
      return weeks;
    },
    // The one day button reachable with Tab; arrow keys move from there.
    focusKey() {
      return this.selectedKey || dateKey(this.year, this.month, 1);
    },
    selectedDay() {
      return this.selectedKey ? this.days[this.selectedKey] || null : null;
    },
    selectedParts() {
      if (!this.selectedKey) return null;
      const [year, month, day] = this.selectedKey.split('-').map(Number);
      return { year, month, day };
    },
    selectedIsToday() {
      return this.selectedKey === this.todayKey;
    },
    selectedDateLabel() {
      if (!this.selectedParts) return '';
      const { year, month, day } = this.selectedParts;
      return new Date(year, month - 1, day).toLocaleDateString('en-US', {
        weekday: 'long',
        month: 'long',
        day: 'numeric',
      });
    },
    selectedColor() {
      return (
        normalizeColor(this.getColorForDate(this.selectedKey)) ||
        normalizeColor(this.selectedDay?.primary_color) ||
        'green'
      );
    },
    // Other observances of the day, skipping ferias and the day's title.
    selectedCommemorations() {
      const day = this.selectedDay;
      if (!day || !Array.isArray(day.commemorations)) return [];
      const title = plainText(day.primary_feast).toLowerCase();
      return day.commemorations.filter(
        (commemoration) =>
          !String(commemoration.rank?.name || '').includes('FERIA') &&
          plainText(commemoration.name).toLowerCase() !== title
      );
    },
    selectedLinks() {
      if (!this.selectedParts) return [];
      const { year, month, day } = this.selectedParts;
      const path = `${year}/${month}/${day}`;
      const family = this.serviceType === 'family';
      const offices = (family ? FAMILY_OFFICES : DAILY_OFFICES).map(
        (office) => ({
          ...office,
          to: `${family ? '/family' : ''}/${office.name}/${path}`,
        })
      );
      return [
        ...offices,
        { text: 'Readings', icon: 'book-text', to: `/readings/${path}` },
      ];
    },
    selectedDayRoute() {
      if (!this.selectedParts) return '/calendar';
      const { year, month, day } = this.selectedParts;
      return `/day/${year}/${month}/${day}/`;
    },
  },
  watch: {
    '$route.params.year': function () {
      this.setCalendar();
    },
    '$route.params.month': function () {
      this.setCalendar();
    },
    '$route.query.subscribe': function (value) {
      if (value === '1') {
        this.openSubscriptionWizardFromQuery();
      }
    },
  },
  async created() {
    // Remember a ?subscribe=1 link now: on a cold load the app clears the
    // query string once settings initialize, before the month has loaded.
    if (this.$route.query.subscribe === '1' || this.pendingSubscriptionPanel) {
      this.pendingSubscriptionPanel = this.$route.query.panel || 'quick';
    }
    this.setCalendar();
  },
  mounted() {
    window.addEventListener(
      'open-calendar-subscription',
      this.handleCalendarSubscriptionEvent
    );
  },
  unmounted() {
    window.removeEventListener(
      'open-calendar-subscription',
      this.handleCalendarSubscriptionEvent
    );
  },
  methods: {
    getCalendarPath(year = this.year, month = this.month) {
      if (year && month) {
        return `/calendar/${year}/${month}/`;
      }
      return '/calendar';
    },
    // Saved only when the reader picks, so "All feasts" stays the default
    // until they choose otherwise. (The old 'includeMinorFeasts' key was
    // written on every visit, so it can't tell a choice from the default.)
    async updateIncludeMinorFeasts() {
      await DynamicStorage.setItem(
        FEAST_FILTER_KEY,
        this.includeMinorFeasts ? 'all' : 'major'
      );
    },
    async setIncludeMinorFeasts(value) {
      this.includeMinorFeasts = Boolean(value);
      await this.updateIncludeMinorFeasts();
    },
    colorOf(commemoration) {
      return normalizeColor(commemoration?.colors?.[0]) || 'white';
    },
    getColorForDate(day) {
      try {
        let commemorations = this.days[day].commemorations;
        if (this.includeMinorFeasts) {
          commemorations = commemorations.filter((commemoration) => {
            return commemoration.rank.name.includes('FERIA') === false;
          });
          if (!commemorations.length) {
            return this.days[day].season.colors[0];
          }
          return commemorations[0].colors[0];
        }
        if (this.days[day].major_feast) {
          return commemorations[0].colors[0];
        }
        return this.days[day].season.colors[0];
      } catch {
        return '';
      }
    },
    // The name shown in a day's cell: major feasts always, lesser
    // commemorations only when "All feasts" is chosen.
    getFeastNameForDate(day) {
      const entry = this.days[day];
      if (!entry) return '';
      if (entry.major_feast) return entry.major_feast;
      if (this.includeMinorFeasts) return entry.major_or_minor_feast || '';
      return '';
    },
    async selectDate(changeType) {
      // The month isn't known until the calendar has loaded.
      if (!this.year && changeType !== 'today') return;
      if (changeType === 'prev-month') {
        if (this.month === 1) {
          this.year -= 1;
          this.month = 12;
        } else {
          this.month -= 1;
        }
      }
      if (changeType === 'next-month') {
        if (this.month === 12) {
          this.year += 1;
          this.month = 1;
        } else {
          this.month += 1;
        }
      }
      if (changeType === 'today') {
        const today = new Date();
        if (
          this.year === today.getFullYear() &&
          this.month === today.getMonth() + 1
        ) {
          this.selectedKey = this.todayKey;
          return;
        }
        this.year = today.getFullYear();
        this.month = today.getMonth() + 1;
      }
      const year = this.year;
      const month = this.month;
      await this.$router.push({ path: this.getCalendarPath(year, month) });
    },
    async setCalendar() {
      // Months can change faster than they load; only the latest request
      // may update the page.
      const token = (this.loadToken = (this.loadToken || 0) + 1);
      const stale = () => token !== this.loadToken;
      this.loading = true;
      this.error = false;
      this.days = {};
      const [feastFilter, serviceType] = await Promise.all([
        DynamicStorage.getItem(FEAST_FILTER_KEY),
        DynamicStorage.getItem('serviceType'),
      ]);
      if (stale()) return;
      this.includeMinorFeasts = feastFilter !== 'major';
      this.serviceType = serviceType === 'family' ? 'family' : 'office';
      let data;
      const today = new Date();
      let year = parseInt(this.$route.params.year);
      let month = parseInt(this.$route.params.month);
      if (!year) {
        year = today.getFullYear();
        month = today.getMonth() + 1;
      } else if (!month) {
        month = 1;
      }
      this.year = year;
      this.month = month;
      this.date = new Date(this.year, this.month - 1, 1);
      // Start on today when it is in view, otherwise on the first.
      this.selectedKey =
        year === today.getFullYear() && month === today.getMonth() + 1
          ? this.todayKey
          : dateKey(year, month, 1);
      try {
        data = await this.$http.get(
          `${import.meta.env.VITE_API_URL}api/v1/calendar/${this.year}-${this.month}`
        );
      } catch {
        if (stale()) return;
        this.error =
          'There was an error retrieving the calendar. Please try again.';
        this.loading = false;
        if (
          this.$route.query.subscribe === '1' ||
          this.pendingSubscriptionPanel
        ) {
          await this.$nextTick();
          await this.openSubscriptionWizardFromQuery();
        }
        return;
      }
      if (stale()) return;
      const days = {};
      data.data.forEach((day) => {
        days[day.date] = day;
      });
      this.days = days;
      this.loading = false;
      if (
        this.$route.query.subscribe === '1' ||
        this.pendingSubscriptionPanel
      ) {
        await this.openSubscriptionWizardFromQuery();
      }
    },
    // A tap chooses a day and shows it below; tapping the chosen day again
    // opens its page.
    async clickDateCell(cell, event) {
      event?.preventDefault();
      if (cell.key !== this.selectedKey) {
        this.selectedKey = cell.key;
        return;
      }
      const [year, month, day] = cell.key.split('-').map(Number);
      await this.$router.push({
        name: 'day',
        params: { year: String(year), month: String(month), day: String(day) },
      });
    },
    onGridKeydown(event) {
      const steps = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7 };
      if (!(event.key in steps) && event.key !== 'Home' && event.key !== 'End')
        return;
      if (!event.target?.dataset?.day) return;
      event.preventDefault();
      const count = new Date(this.year, this.month, 0).getDate();
      const current = Number(event.target.dataset.day.split('-')[2]);
      let next = current + (steps[event.key] || 0);
      if (event.key === 'Home') next = 1;
      if (event.key === 'End') next = count;
      next = Math.min(count, Math.max(1, next));
      this.selectedKey = dateKey(this.year, this.month, next);
      this.$nextTick(() => {
        this.$el?.querySelector?.(`[data-day="${this.selectedKey}"]`)?.focus();
      });
    },
    async openSubscriptionWizard(options = {}) {
      for (let i = 0; i < 6; i += 1) {
        await this.$nextTick();
        if (this.$refs.calendarSubscriptionWizard) {
          break;
        }
      }
      if (!this.$refs.calendarSubscriptionWizard) {
        return;
      }

      const { source = 'calendar', ...wizardOptions } = options;
      if (!wizardOptions.scope) {
        wizardOptions.scope = getCalendarWizardDefaultScope({
          source,
          includeMinorFeasts: this.includeMinorFeasts,
        });
      }

      if (wizardOptions.mode === 'quick') {
        this.$refs.calendarSubscriptionWizard.openQuickLinks();
        return;
      }

      this.$refs.calendarSubscriptionWizard.openWizard(wizardOptions);
    },
    async openSubscriptionWizardFromQuery() {
      const panelMode =
        this.$route.query.panel ||
        this.pendingSubscriptionPanel ||
        window.sessionStorage.getItem('calendarSubscriptionPanelMode') ||
        'quick';
      this.pendingSubscriptionPanel = null;

      await this.openSubscriptionWizard({
        source: 'menu',
        mode: panelMode,
      });
      const query = { ...this.$route.query };
      delete query.subscribe;
      delete query.panel;
      window.sessionStorage.removeItem('calendarSubscriptionPanelMode');
      await this.$router.replace({
        path: this.getCalendarPath(this.year, this.month),
        query,
      });
    },
    async handleCalendarSubscriptionEvent(event) {
      const detail = event?.detail || {};
      await this.openSubscriptionWizard({
        source: 'menu',
        ...detail,
      });
    },
  },
};
</script>

<style scoped>
.page-header {
  margin-bottom: var(--space-5);
}

/* ── Toolbar: ‹ October 2026 ›, the feast filter, Today ── */
.calendar-toolbar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  grid-template-areas:
    'nav nav'
    'filter today';
  align-items: center;
  gap: var(--space-3) var(--space-3);
  margin-bottom: var(--space-4);
}

.month-nav {
  grid-area: nav;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  min-width: 0;
}

.month-nav__title {
  min-width: 0;
  flex: 0 1 14rem;
  font-size: var(--text-xl);
  font-weight: 400;
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
  line-height: 1.1;
  text-align: center;
  color: var(--ink);
}

.month-nav__step {
  color: var(--ink-soft);
}

.calendar-toolbar__filter {
  grid-area: filter;
  justify-self: start;
}

.calendar-toolbar__today {
  grid-area: today;
  justify-self: end;
}

/* The smallest phones: one control per row so nothing is truncated. */
@media (max-width: 419px) {
  .calendar-toolbar {
    grid-template-columns: minmax(0, 1fr);
    grid-template-areas:
      'nav'
      'filter'
      'today';
    justify-items: center;
  }

  .calendar-toolbar__filter,
  .calendar-toolbar__today {
    justify-self: center;
  }
}

@media (min-width: 768px) {
  .calendar-toolbar {
    grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
    grid-template-areas: 'filter nav today';
  }
}

.calendar-error {
  margin-bottom: var(--space-4);
}

/* ── Layout: grid, then the chosen day (beside it on wide screens) ── */
.calendar-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: var(--space-5);
}

@media (min-width: 1024px) {
  .calendar-layout {
    grid-template-columns: minmax(0, 1fr) 17.5rem;
    align-items: start;
    gap: var(--space-6);
  }
}

/* ── Month grid ──────────────────────────────────────── */
.month {
  min-width: 0;
  border-bottom: 1px solid var(--rule);
}

.month__row {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  border-top: 1px solid var(--rule);
}

.month__weekdays {
  border-top: 0;
}

.month__weekday {
  padding: var(--space-1) 0 var(--space-2);
  font-size: var(--text-sm);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.12em;
  color: var(--ink-faint);
  text-align: center;
}

.weekday--long {
  display: none;
}

.month__cell {
  min-width: 0;
}

.day {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  height: 100%;
  min-height: 3.25rem;
  padding: var(--space-2) 0 var(--space-1);
  color: var(--ink);
  text-align: center;
  transition: background-color var(--duration) var(--ease);
}

.day:hover {
  background-color: var(--paper-sunken);
}

.day:focus-visible {
  outline: none;
  box-shadow: inset 0 0 0 2px var(--accent);
  border-radius: 0;
}

.day__head {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.3rem;
}

.day__number {
  display: grid;
  place-items: center;
  min-width: 1.85rem;
  height: 1.85rem;
  padding-top: 0.1em;
  border-radius: 50%;
  font-size: var(--text-md);
  line-height: 1;
  font-variant-numeric: lining-nums tabular-nums;
}

/* The color of the day: a small square, as on the office page. Feast days
   draw it as a short bar so they stand out in the compact grid. */
.day__swatch {
  display: block;
  width: 0.45rem;
  height: 0.45rem;
  border-radius: 1px;
}

.day.has-feast .day__swatch {
  width: 1.1rem;
  height: 0.25rem;
}

.day__feast {
  display: none;
}

.day.is-today .day__number {
  background-color: var(--accent);
  color: var(--on-accent);
}

.day.is-selected {
  background-color: var(--accent-wash);
  box-shadow: inset 0 -2px 0 var(--accent);
}

/* Phones: let the grid run to the screen edges so each day is a full
   tap target. */
@media (max-width: 479px) {
  .month {
    margin-inline: calc(-1 * var(--gutter));
  }
}

@media (min-width: 640px) {
  .weekday--long {
    display: inline;
  }

  .weekday--narrow {
    display: none;
  }

  .month__weekday {
    padding-inline: var(--space-2);
    text-align: left;
  }

  .month__cell + .month__cell {
    border-left: 1px solid var(--rule);
  }

  .day {
    align-items: stretch;
    gap: var(--space-1);
    min-height: 6.75rem;
    padding: var(--space-2);
    text-align: left;
  }

  .day__head {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }

  .day__number {
    margin: -0.2rem 0 0 -0.3rem;
  }

  .day.has-feast .day__swatch {
    width: 0.45rem;
    height: 0.45rem;
  }

  .day__feast {
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 4;
    line-clamp: 4;
    overflow: hidden;
    font-size: var(--text-xs);
    line-height: 1.3;
    font-style: italic;
    color: var(--ink-soft);
    overflow-wrap: anywhere;
    hyphens: auto;
  }

  .day.is-major .day__feast {
    font-style: normal;
    color: var(--ink);
  }
}

@media (min-width: 1280px) {
  .day {
    min-height: 7.5rem;
  }
}

/* ── The chosen day ──────────────────────────────────── */
.day-detail {
  min-width: 0;
  text-align: left;
}

@media (min-width: 1024px) {
  .day-detail {
    position: sticky;
    top: calc(var(--header-height) + env(safe-area-inset-top) + 1rem);
    padding-left: var(--space-5);
    border-left: 1px solid var(--rule);
  }
}

.day-detail__date {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-md);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.12em;
  color: var(--ink-faint);
}

.day-detail__feast {
  margin-top: var(--space-2);
  font-size: var(--text-lg);
  font-style: italic;
  line-height: 1.3;
  color: var(--ink);
  text-wrap: pretty;
}

.day-detail__swatch {
  display: inline-block;
  width: 0.55em;
  height: 0.55em;
  margin-right: 0.45em;
  border-radius: 2px;
  vertical-align: 0.08em;
}

.day-detail__swatch--small {
  flex-shrink: 0;
  margin: 0.45em 0 0;
}

.day-detail__season {
  margin-top: var(--space-1);
  font-size: var(--text-sm);
  color: var(--ink-faint);
}

.day-detail__also {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin-top: var(--space-4);
  padding-top: var(--space-3);
  border-top: 1px solid var(--rule);
  font-size: var(--text-sm);
  line-height: 1.4;
}

.day-detail__also li {
  display: flex;
  gap: var(--space-2);
}

.day-detail__also a {
  color: var(--ink-soft);
  text-decoration-color: var(--rule-strong);
}

.day-detail__also a:hover {
  color: var(--ink);
}

.day-detail__pray {
  margin-top: var(--space-4);
  padding-top: var(--space-3);
  border-top: 1px solid var(--rule);
}

.day-detail__label {
  font-size: var(--text-sm);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.12em;
  color: var(--ink-faint);
}

.day-links {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(8.5rem, 1fr));
  gap: 0 var(--space-3);
  margin-top: var(--space-1);
}

@media (min-width: 1024px) {
  .day-links {
    grid-template-columns: 1fr;
  }
}

.day-link {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-height: 2.75rem;
  border-bottom: 1px solid var(--rule);
  color: var(--ink);
  text-decoration: none;
}

.day-link:hover {
  color: var(--accent);
}

.day-link__icon {
  color: var(--accent);
}

.day-detail__more {
  display: inline-flex;
  align-items: center;
  min-height: 2.75rem;
  margin-top: var(--space-1);
  font-style: italic;
}

/* ── Subscribe ───────────────────────────────────────── */
.divider {
  max-width: 24rem;
  margin: var(--space-7) auto var(--space-5);
}

.subscribe {
  max-width: 36rem;
  margin: 0 auto;
  text-align: center;
}

.subscribe__text {
  margin: var(--space-2) auto var(--space-4);
  color: var(--ink-soft);
  font-size: var(--text-md);
  line-height: var(--leading-prose);
}
</style>
