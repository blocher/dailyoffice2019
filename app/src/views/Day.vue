<template>
  <div class="small-container">
    <PageNotFound v-if="notFound"/>
    <div v-if="!notFound">
      <Loading v-if="loading"/>
      <div
          v-if="error" class="alert-danger"
      >
        {{ error }}
      </div>
      <div
          v-if="!loading" class="day"
      >
        <CalendarCard
            v-if="!loading"
            :office="office"
            :calendar-date="calendarDate"
            :card="card"
        />
        <OfficeNav
            :calendar-date="calendarDate" :service-type="currentServiceType"
        />
      </div>
    </div>
  </div>
</template>
.el-row
<script>
// @ is an alias to /src
import setCalendarDate from "@/helpers/setCalendarDate";
import OfficeNav from "@/components/OfficeNav";
import PageNotFound from "@/views/PageNotFound";
import {DynamicStorage} from "@/helpers/storage";

export default {
  name: "Calendar",
  components: {OfficeNav, PageNotFound},
  properties: {
    office: null,
    serviceType: {
      type: String,
      default: "office",
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
      currentServiceType: "office",
      notFound: false,
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
    if (this.$route.params.serviceType) {
      this.currentServiceType = this.$route.params.serviceType;
    } else if (!this.$route.params.office) {
      this.currentServiceType = await DynamicStorage.getItem("serviceType") || "office";
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
            `${process.env.VUE_APP_API_URL}api/v1/calendar/${this.year}-${this.month}-${this.day}`
        );
      } catch (e) {
        if (e.response.status == "404") {
          this.notFound = true;
          return;
        }
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
<style lang="scss" scoped></style>
