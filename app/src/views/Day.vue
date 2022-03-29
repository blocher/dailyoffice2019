<template>
  <div class="small-container">
    <Loading v-if="loading" />
    <div v-if="error" class="alert-danger">{{ error }}</div>
    <div v-if="!loading" class="day">
      <CalendarCard
        v-if="!loading"
        :office="office"
        :calendar-date="calendarDate"
        :card="card"
      />
      <OfficeNav :calendar-date="calendarDate" :service-type="serviceType" />
    </div>
  </div>
</template>
.el-row
<style lang="scss" scoped></style>
<script>
// @ is an alias to /src
import setCalendarDate from "@/helpers/setCalendarDate";
import OfficeNav from "@/components/OfficeNav";

export default {
  name: "Calendar",
  components: { OfficeNav },
  props: ["office"],
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
      serviceType: "office",
    };
  },
  watch: {
    "$route.params.year": function () {
      this.setDay();
    },
    "$route.params.month": function () {
      this.setDay();
    },
    "$route.params.day": function () {
      this.setDay();
    },
  },
  async created() {
    this.setDay();
    this.serviceType = localStorage.getItem("serviceType") || "office";
  },
  methods: {
    scrollToTop() {
      window.scrollTo(0, 0);
    },
    setDay: async function () {
      this.loading = true;
      this.calendarDate = setCalendarDate(this.$route);
      if (!this.calendarDate) {
        await this.$router.push({ name: "not_found" });
        return;
      }
      this.day = this.$route.params.day;
      this.month = this.$route.params.month;
      this.year = this.$route.params.year;
      let data = null;
      try {
        data = await this.$http.get(
          `${process.env.VUE_APP_API_URL}api/v1/calendar/${this.year}-${this.month}-${this.day}`
        );
      } catch (e) {
        this.error =
          "There was an error retrieving this calendar. Please try again.";
        this.loading = false;
        return;
      }
      this.card = data.data;

      this.scrollToTop();
      this.loading = false;
    },
  },
};
</script>
