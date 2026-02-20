<template>
  <div class="small-container">
    <PageNotFound v-if="notFound" />
    <div v-if="!notFound">
      <Loading v-if="loading" />
      <div v-if="error" class="alert-danger">
        {{ error }}
      </div>
      <div v-if="!loading" class="day">
        <CalendarCard
          v-if="!loading"
          :calendar-date="calendarDate"
          :card="card"
        />
        <OfficeNav
          :calendar-date="calendarDate"
          :service-type="currentServiceType"
          :selected-office="'day'"
        />
      </div>
    </div>
  </div>
</template>
.el-row
<script>
// @ is an alias to /src
import setCalendarDate from '@/helpers/setCalendarDate';
import OfficeNav from '@/components/OfficeNav.vue';
import PageNotFound from '@/views/PageNotFound.vue';
import { DynamicStorage } from '@/helpers/storage';
import { resolveColorFromCard, setSeasonAccent } from '@/helpers/seasonAccent';
import CalendarCard from '@/components/CalendarCard.vue';
import Loading from '@/components/Loading.vue';

export default {
  name: 'Calendar',
  components: { OfficeNav, PageNotFound, CalendarCard, Loading },
  properties: {
    office: null,
    serviceType: {
      type: String,
      default: 'office',
    },
  },
  data() {
    return {
      year: null,
      month: null,
      day: null,
      date: null,
      card: null,
      loading: true,
      calendarDate: null,
      error: null,
      links: [],
      dayLinks: [],
      currentServiceType: 'office',
      notFound: false,
    };
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
    scrollToTop() {
      window.scrollTo(0, 0);
    },
    setDay: async function () {
      this.loading = true;
      this.calendarDate = setCalendarDate(this.$route);
      if (!this.calendarDate) {
        this.notFound = true;
        return;
      }
      this.day = this.$route.params.day;
      this.month = this.$route.params.month;
      this.year = this.$route.params.year;
      let data = null;
      try {
        data = await this.$http.get(
          `${import.meta.env.VITE_API_URL}api/v1/calendar/${this.year}-${this.month}-${this.day}`
        );
      } catch (e) {
        if (e.response.status == '404') {
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
<style lang="scss" scoped></style>
