<template>
  <div>
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
    };
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
      const offices = [
        'morning_prayer',
        'evening_prayer',
        'midday_prayer',
        'compline',
        'early_evening_prayer',
        'close_of_day_prayer',
      ];
      const serviceParam = this.$route.params.serviceType;
      this.office = this.$route.params.office;
      this.notFound = false;
      if (serviceParam && !['office', 'family'].includes(serviceParam)) {
        // A bare office name like /morning_prayer is caught by
        // /:serviceType; anything else there is not a page.
        if (!this.office && offices.includes(serviceParam)) {
          this.office = serviceParam;
          // Early Evening and Close of Day are Family Prayer offices.
          if (
            ['early_evening_prayer', 'close_of_day_prayer'].includes(
              serviceParam
            )
          ) {
            this.currentServiceType = 'family';
          }
        } else {
          this.notFound = true;
          document.title = 'Page not found | The Daily Office';
          return;
        }
      }
      if (!this.office) {
        this.setCurrentOffice();
      }
      if (!offices.includes(this.office)) {
        this.notFound = true;
        document.title = 'Page not found | The Daily Office';
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
