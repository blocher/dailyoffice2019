<template>
  <Office
    v-if="!notFound"
    :service-type="serviceType"
    :office="office"
    :calendar-date="calendarDate"
  />
  <PageNotFound v-if="notFound" />
</template>

<script>
// @ is an alias to /src
import Office from '@/views/Office.vue';
import setCalendarDate from '@/helpers/setCalendarDate';
import PageNotFound from '@/views/PageNotFound.vue';

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
      calendarDate: null,
      serviceType: 'office',
      notFound: false,
    };
  },
  async created() {
    this.serviceType = this.$route.params.serviceType || 'office';
    this.office = this.$route.params.office;

    this.calendarDate = setCalendarDate(this.$route);
    if (!this.calendarDate) {
      this.notFound = true;
      return;
    }
  },
};
</script>
