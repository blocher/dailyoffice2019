<template>
  <PageNotFound v-if="notFound" />
  <div v-else class="page day-page">
    <header class="page-header">
      <p class="eyebrow">{{ seasonName || 'The Christian Year' }}</p>
      <h1 class="page-title">{{ formattedDate }}</h1>
      <nav v-if="calendarDate" class="day-step" aria-label="Other days">
        <router-link :to="dayPath(-1)" class="day-step__link">
          <UiIcon name="chevron-left" /> Previous day
        </router-link>
        <router-link v-if="!isToday" :to="todayPath" class="day-step__link">
          Today
        </router-link>
        <router-link :to="dayPath(1)" class="day-step__link">
          Next day <UiIcon name="chevron-right" />
        </router-link>
      </nav>
    </header>

    <Loading v-if="loading" />
    <UiAlert v-if="error" tone="error" :title="error" />

    <template v-if="!loading">
      <CalendarCard v-if="card" :calendar-date="calendarDate" :card="card" />

      <div class="divider" aria-hidden="true"><Ornament glyph="o" /></div>

      <section class="day-pray" aria-labelledby="day-pray-title">
        <h2 id="day-pray-title" class="day-pray__title">Pray this day</h2>
        <OfficeNav
          :calendar-date="calendarDate"
          :service-type="currentServiceType"
          :selected-office="'day'"
          :show-day-line="false"
        />
      </section>

      <div class="day-tools" role="toolbar" aria-label="More for this day">
        <router-link :to="readingsLink" class="day-tool">
          <UiIcon name="book-text" />
          Readings
        </router-link>
        <router-link :to="calendarLink" class="day-tool">
          <UiIcon name="calendar" />
          {{ monthName }}
        </router-link>
        <button type="button" class="day-tool" @click="openPanel('display')">
          <span class="day-tool__glyph" aria-hidden="true">Aa</span>
          Display
        </button>
      </div>
    </template>
  </div>
</template>

<script>
// @ is an alias to /src
import setCalendarDate from '@/helpers/setCalendarDate';
import OfficeNav from '@/components/OfficeNav.vue';
import PageNotFound from '@/views/PageNotFound.vue';
import { DynamicStorage } from '@/helpers/storage';
import { resolveColorFromCard, setSeasonAccent } from '@/helpers/seasonAccent';
import { openPanel } from '@/helpers/panels';
import CalendarCard from '@/components/CalendarCard.vue';
import Loading from '@/components/Loading.vue';

export default {
  name: 'Day',
  components: {
    OfficeNav,
    PageNotFound,
    CalendarCard,
    Loading,
  },
  data() {
    return {
      year: null,
      month: null,
      day: null,
      card: null,
      loading: true,
      calendarDate: null,
      error: null,
      currentServiceType: 'office',
      notFound: false,
    };
  },
  computed: {
    formattedDate() {
      if (!this.calendarDate) return 'The Day';
      return this.calendarDate.toLocaleDateString('en-US', {
        weekday: 'long',
        month: 'long',
        day: 'numeric',
        year: 'numeric',
      });
    },
    monthName() {
      if (!this.calendarDate) return 'Calendar';
      return this.calendarDate.toLocaleDateString('en-US', {
        month: 'long',
        year: 'numeric',
      });
    },
    seasonName() {
      return this.card?.season?.name || '';
    },
    isToday() {
      return (
        this.calendarDate &&
        this.calendarDate.toDateString() === new Date().toDateString()
      );
    },
    todayPath() {
      const d = new Date();
      return `/day/${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()}/`;
    },
    readingsLink() {
      const d = this.calendarDate;
      return `/readings/${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()}`;
    },
    calendarLink() {
      const d = this.calendarDate;
      return `/calendar/${d.getFullYear()}/${d.getMonth() + 1}/`;
    },
  },
  watch: {
    '$route.params.year': function () {
      this.setDay();
    },
    '$route.params.month': function () {
      this.setDay();
    },
    '$route.params.day': function () {
      this.setDay();
    },
  },
  async created() {
    if (this.$route.params.serviceType) {
      this.currentServiceType = this.$route.params.serviceType;
    } else if (!this.$route.params.office) {
      this.currentServiceType =
        (await DynamicStorage.getItem('serviceType')) || 'office';
    }
    await this.setDay();
  },
  methods: {
    dayPath(offset) {
      const d = new Date(this.calendarDate);
      d.setDate(d.getDate() + offset);
      return `/day/${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()}/`;
    },
    openPanel,
    scrollToTop() {
      window.scrollTo(0, 0);
    },
    setDay: async function () {
      this.loading = true;
      this.error = null;
      this.calendarDate = setCalendarDate(this.$route);
      if (!this.calendarDate) {
        this.notFound = true;
        return;
      }
      document.title = `${this.formattedDate} | The Daily Office`;
      this.day = this.$route.params.day;
      this.month = this.$route.params.month;
      this.year = this.$route.params.year;
      let data;
      try {
        data = await this.$http.get(
          `${import.meta.env.VITE_API_URL}api/v1/calendar/${this.year}-${this.month}-${this.day}`
        );
      } catch (e) {
        if (String(e?.response?.status) === '404') {
          this.notFound = true;
          return;
        }
        this.error =
          'There was an error retrieving this calendar. Please try again.';
        this.loading = false;
        return;
      }
      this.card = data.data;
      this.applySeasonAccentFromCard(this.card);

      this.scrollToTop();
      this.loading = false;
    },
    applySeasonAccentFromCard(card) {
      const liturgicalColor = resolveColorFromCard(card, 'day');
      if (liturgicalColor) {
        setSeasonAccent(liturgicalColor);
      }
    },
  },
};
</script>

<style scoped>
.day-step {
  display: flex;
  justify-content: center;
  gap: var(--space-5);
  margin-top: var(--space-2);
  font-size: var(--text-sm);
}

.day-step__link {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  min-height: 2.75rem;
  color: var(--ink-soft);
  text-decoration: none;
}

.day-step__link:hover {
  color: var(--accent);
}

.page-title {
  text-wrap: balance;
}

.divider {
  max-width: 20rem;
  margin-inline: auto;
}

.day-pray__title {
  margin-bottom: var(--space-3);
  font-size: var(--text-md);
  font-weight: 400;
  font-variant-caps: all-small-caps;
  letter-spacing: 0.12em;
  color: var(--ink-faint);
  text-align: center;
}

/* Quiet links under the offices, matching the office page's tools. */
.day-tools {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--space-2);
  margin-top: var(--space-6);
}

.day-tool {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  min-height: 2.75rem;
  padding: 0.2rem 0.9rem;
  border: 1px solid var(--rule);
  border-radius: var(--radius-pill);
  background-color: var(--paper);
  color: var(--ink-soft);
  font-size: var(--text-sm);
  text-decoration: none;
  transition:
    border-color var(--duration) var(--ease),
    color var(--duration) var(--ease);
}

.day-tool:hover {
  border-color: var(--rule-strong);
  color: var(--ink);
}

.day-tool .ui-icon {
  color: var(--accent);
}

.day-tool__glyph {
  font-size: 1.05em;
  line-height: 1;
}
</style>
