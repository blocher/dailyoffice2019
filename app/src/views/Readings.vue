<template>
  <div class="small-container home office">
    <Loading v-if="loading"/>
    <div id="readings" :v-if="!loading && !error">
      <CalendarCard
          :calendar-date="calendarDate"
      />
      <OfficeNav
          :calendar-date="calendarDate"
      />
    </div>
    <h1>Readings</h1>
  </div>
</template>

<style scoped>
.el-alert {
  margin-top: 2em;
}
</style>

<script>
// @ is an alias to /src
import Loading from "@/components/Loading";
import setCalendarDate from "@/helpers/setCalendarDate";
import CalendarCard from "@/components/CalendarCard";
import OfficeNav from "@/components/OfficeNav";

export default {
  name: "Readings",
  components: {
    Loading,
    CalendarCard,
    OfficeNav
  },
  props: {},
  data() {
    return {
      loading: true,
      error: false,
      calendarDate: null,
    };
  },
  mounted() {
  },

  async created() {
    let data = null;
    this.calendarDate = setCalendarDate(this.$route);
    try {
      const today_str =
          this.calendarDate.getFullYear() +
          "-" +
          (this.calendarDate.getMonth() + 1) +
          "-" +
          this.calendarDate.getDate();
      data = await this.$http.get(
          `${process.env.VUE_APP_API_URL}api/v1/readings/${this.office}/` +
          today_str
      );
    } catch (e) {
      this.error =
          "There was an error retrieving the office. Please try again.";
      this.loading = false;
      return;
    }
    this.error = false;
    this.loading = false;
  },
  methods: {},
};
</script>
