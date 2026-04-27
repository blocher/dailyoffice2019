<template>
  <h1>Calendar</h1>
  <section
    class="p-4 mx-3 mb-4 rounded-2xl border shadow-sm border-slate-200 bg-white/90 dark:border-slate-700 dark:bg-slate-900/65 sm:mx-4 sm:p-5"
  >
    <div
      class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"
    >
      <div class="min-w-0">
        <p
          class="m-0 text-sm font-semibold tracking-tight text-slate-900 dark:text-white"
        >
          Susbcribe in your calendar app
        </p>
        <p
          class="m-0 mt-1 text-sm leading-6 text-slate-600 dark:text-slate-300"
        >
          Add this liturgical calendar in your preferred calendar app such as
          Apple Calendar, Microsoft Outlook, or Google Calendar
        </p>
      </div>
      <CalendarSubscriptionWizard
        ref="calendarSubscriptionWizard"
        :default-scope="calendarWizardDefaultScope"
        :include-minor-feasts="includeMinorFeasts"
      />
    </div>
  </section>
  <Loading v-if="loading" />
  <div class="text-center full-width">
    <el-switch
      v-model="includeMinorFeasts"
      size="large"
      active-text="Show All Feasts"
      inactive-text="Show Major Feasts Only"
      @change="updateIncludeMinorFeasts"
    />
  </div>
  <el-calendar v-if="!loading" v-model="date">
    <template #header="{ date }">
      <span>{{ date }}</span>

      <el-button-group>
        <el-button size="small" @click="selectDate('today')"> Now</el-button>
        <el-button size="small" @click="selectDate('prev-month')">
          Previous Month
        </el-button>
        <el-button size="small" @click="selectDate('next-month')">
          Next Month
        </el-button>
      </el-button-group>
    </template>
    <template #date-cell="{ data }">
      <div
        class="dateCellWrapper"
        :class="getColorForDate(data.day)"
        @click="clickDateCell(data, $event)"
      >
        <p>{{ parseInt(data.day.split('-')[2]) }}</p>
        <p class="calendarText" v-html="getFeastNameForDate(data.day)"></p>
      </div>
    </template>
  </el-calendar>
</template>

<script>
import CalendarSubscriptionWizard from '@/components/CalendarSubscriptionWizard.vue';
import Loading from '@/components/Loading.vue';
import { getCalendarWizardDefaultScope } from '@/helpers/calendarSubscription';
import { DynamicStorage } from '@/helpers/storage';

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
      includeMinorFeasts: false,
    };
  },
  computed: {
    calendarWizardDefaultScope() {
      return getCalendarWizardDefaultScope({
        source: 'calendar',
        includeMinorFeasts: this.includeMinorFeasts,
      });
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
    async updateIncludeMinorFeasts() {
      const includeMinorFeasts = this.includeMinorFeasts ? 'true' : 'false';
      await DynamicStorage.setItem('includeMinorFeasts', includeMinorFeasts);
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
    getFeastNameForDate(day) {
      let feast = '';
      let bold = false;
      try {
        feast = this.days[day].major_feast;
        if (feast) {
          bold = true;
        }
      } catch {
        feast = '';
      }
      if (this.includeMinorFeasts && !feast) {
        try {
          feast = this.days[day].major_or_minor_feast;
        } catch {
          feast = '';
        }
      }
      if (bold) {
        return `<strong>${feast}</strong>`;
      }
      return feast;
    },
    async selectDate(changeType) {
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
        this.year = today.getFullYear();
        this.month = today.getMonth() + 1;
      }
      const year = this.year;
      const month = this.month;
      await this.$router.push({ path: this.getCalendarPath(year, month) });
    },
    async setCalendar() {
      this.loading = true;
      this.days = {};
      const includeMinorFeasts =
        (await DynamicStorage.getItem('includeMinorFeasts')) || 'false';
      this.includeMinorFeasts = includeMinorFeasts === 'true';
      this.updateIncludeMinorFeasts();
      let data = null;
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
      try {
        data = await this.$http.get(
          `${import.meta.env.VITE_API_URL}api/v1/calendar/${this.year}-${this.month}`
        );
      } catch {
        this.error =
          'There was an error retrieving the office. Please try again.';
        this.loading = false;
        if (this.$route.query.subscribe === '1') {
          await this.$nextTick();
          await this.openSubscriptionWizardFromQuery();
        }
        return;
      }
      data.data.forEach((day) => {
        const dateString = day.date;
        this.days[dateString] = day;
      });
      this.loading = false;
      if (this.$route.query.subscribe === '1') {
        await this.openSubscriptionWizardFromQuery();
      }
    },
    async clickDateCell(data, event) {
      event.preventDefault();
      event.stopPropagation();
      const day = data.day.split('-');
      await this.$router.push({
        name: 'day',
        params: { year: day[0], month: day[1], day: day[2] },
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
        window.sessionStorage.getItem('calendarSubscriptionPanelMode') ||
        'quick';

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

<style lang="scss">
.dateCellWrapper {
  @media only screen and (max-width: 733px) {
    .calendarText {
      font-size: 0.4rem;
    }
  }
}

td {
  height: 1px !important;
}

.el-calendar,
.el-calendar-table td.is-selected {
  background-color: var(--color-bg) !important;
}

.el-calendar-day {
  min-height: 75px;
  height: 100% !important;
  padding: 0 !important;
  display: flex;
  margin-bottom: auto;
  color: var(--el-text-color-primary);

  &:hover {
    color: var(--font-on-white-background);
  }

  p {
    line-height: 1.1em;
  }
}

.dateCellWrapper {
  padding: 8px;
  height: 100%;
  width: 100%;
  margin-bottom: auto;
  @media only screen and (max-width: 733px) {
    padding: 3px;
  }
}

.el-calendar-table__row td {
  border: 1px solid var(--el-border-color, black);
}

.red {
  background-color: #c21c13;
  color: white;
}

.green {
  background-color: #077339;
  color: white;
}

.white {
  background-color: #f5f1e8;
  color: #333;
}

:root.dark .white {
  background-color: #3a3631;
  color: #e5e7eb;
}

.purple {
  background-color: #64147d;
  color: white;
}

.black {
  background-color: #1a1a1a;
  color: white;
}

:root.dark .black {
  background-color: #111;
  color: #d1d5db;
}

.rose {
  background-color: pink;
  color: #333;
}

:root.dark .rose {
  background-color: #9f3050;
  color: #fce4ec;
}
</style>
