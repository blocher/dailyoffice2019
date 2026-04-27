<template>
  <div>
    <div
      v-if="showCalendarAppNudge"
      class="mx-auto mt-2 mb-3 max-w-[700px] px-4 sm:mt-3 sm:mb-4 sm:px-5"
    >
      <div
        class="flex flex-wrap items-center gap-2 rounded-lg border border-slate-200/90 bg-slate-50/90 px-3 py-2.5 text-left text-slate-600 shadow-sm dark:border-slate-600/50 dark:bg-slate-800/40 dark:text-slate-300 sm:gap-3"
        role="region"
        aria-label="New feature"
      >
        <span
          class="inline-flex shrink-0 items-center rounded-md bg-emerald-100/90 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-200"
        >
          New
        </span>
        <p class="m-0 min-w-0 flex-1 text-xs leading-snug sm:text-sm">
          <router-link
            class="font-medium text-(--accent-color) underline decoration-(--accent-color)/30 underline-offset-2 transition hover:decoration-(--accent-color)"
            :to="{
              path: '/calendar',
              query: { subscribe: '1', panel: 'quick' },
            }"
          >
            Add the liturgical calendar to your calendar app
          </router-link>
        </p>
        <button
          type="button"
          class="ml-auto shrink-0 rounded-md px-2 py-1 text-sm leading-none text-slate-400 transition hover:bg-slate-200/80 hover:text-slate-700 dark:hover:bg-slate-700/60 dark:hover:text-slate-200"
          aria-label="Dismiss"
          @click="dismissCalendarAppNudge"
        >
          ×
        </button>
      </div>
    </div>
    <Office
      v-if="office && !notFound"
      :key="key"
      :office="office"
      :calendar-date="calendarDate"
      :service-type="currentServiceType"
    />
    <PageNotFound v-if="notFound" />
  </div>
</template>

<script>
// @ is an alias to /src
import Office from '@/views/Office.vue';
import PageNotFound from '@/views/PageNotFound.vue';
import { DynamicStorage } from '@/helpers/storage';

export default {
  name: 'Today',
  components: {
    Office,
    PageNotFound,
  },
  data() {
    return {
      counter: 0,
      modules: null,
      loading: true,
      office: null,
      year: 0,
      month: 0,
      day: 0,
      key: null,
      calendarDate: null,
      currentServiceType: 'office',
      notFound: false,
      calendarAppNudgeDismissed: false,
    };
  },

  computed: {
    showCalendarAppNudge() {
      return this.$route.name === 'Home' && !this.calendarAppNudgeDismissed;
    },
  },

  watch: {
    $route(to) {
      if (to.params.serviceType) {
        if (['office', 'family'].includes(to.params.serviceType)) {
          this.currentServiceType = to.params.serviceType;
          DynamicStorage.setItem('serviceType', this.currentServiceType);
        } else {
          this.currentServiceType = 'office';
        }
      } else if (!to.params.office) {
        DynamicStorage.getItem('serviceType').then((val) => {
          this.currentServiceType = val || 'office';
        });
      }
      this.setDate();
    },
  },
  async created() {
    if (this.$route.params.serviceType) {
      if (['office', 'family'].includes(this.$route.params.serviceType)) {
        this.currentServiceType = this.$route.params.serviceType;
        DynamicStorage.setItem('serviceType', this.currentServiceType);
      } else {
        // If it's something like /morning_prayer which got caught by /:serviceType
        this.currentServiceType = 'office';
      }
    } else if (!this.$route.params.office) {
      this.currentServiceType =
        (await DynamicStorage.getItem('serviceType')) || 'office';
    }
    if (typeof window !== 'undefined' && window.localStorage) {
      this.calendarAppNudgeDismissed =
        window.localStorage.getItem('homeCalendarAppNudgeDismissed') === '1';
    }
    this.setDate();
  },
  properties: {
    office: null,
    forward: null,
    serviceType: {
      type: String,
      default: 'office',
    },
  },
  methods: {
    dismissCalendarAppNudge() {
      this.calendarAppNudgeDismissed = true;
      if (typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.setItem('homeCalendarAppNudgeDismissed', '1');
      }
    },
    setCurrentOffice() {
      const now = new Date();
      const hour = now.getHours();
      if (hour < 4) {
        this.office =
          this.currentServiceType == 'family'
            ? 'close_of_day_prayer'
            : 'compline';
        this.forward = 'yesterday';
        return;
      }
      if (hour >= 4 && hour < 11) {
        this.office = 'morning_prayer';
        return;
      }
      if (hour >= 11 && hour < 15) {
        this.office = 'midday_prayer';
        return;
      }
      if (hour >= 15 && hour < 20) {
        this.office =
          this.currentServiceType == 'family'
            ? 'early_evening_prayer'
            : 'evening_prayer';
        return;
      }
      if (hour >= 20) {
        this.office =
          this.currentServiceType == 'family'
            ? 'close_of_day_prayer'
            : 'compline';
        return;
      }
    },
    async setDate() {
      this.forward = this.$route.params.forward;
      const today = new Date();
      this.office = this.$route.params.office;
      if (!this.office) {
        this.setCurrentOffice();
      }
      if (
        ![
          'morning_prayer',
          'evening_prayer',
          'midday_prayer',
          'compline',
          'early_evening_prayer',
          'close_of_day_prayer',
        ].includes(this.office)
      ) {
        this.notFound = true;
        return;
      }
      if (this.forward === 'tomorrow') {
        today.setDate(today.getDate() + 1);
      }
      if (this.forward === 'yesterday') {
        today.setDate(today.getDate() - 1);
      }
      this.calendarDate = today;
      this.key = `${this.office}-${this.calendarDate}`;
    },
  },
};
</script>
