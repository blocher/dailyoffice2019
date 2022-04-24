<template>
  <Office
      v-if="!notFound"
      :key="key"
      :office="office"
      :calendar-date="calendarDate"
      :service-type="currentServiceType"
  />
  <PageNotFound v-if="notFound"/>
</template>

<script>
// @ is an alias to /src
import Office from "@/views/Office";
import PageNotFound from "@/views/PageNotFound";

export default {
  name: "Today",
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
      currentServiceType: "office",
      notFound: false,
    };
  },

  watch: {
    "$route.params.office": function () {
      this.setDate();
    },
    "$route.params.forward": function () {
      this.setDate();
    },
  },
  async created() {
    if (this.$route.params.serviceType) {
      this.currentServiceType = this.$route.params.serviceType;
    } else if (!this.$route.params.office) {
      this.currentServiceType = localStorage.getItem("serviceType") || "office";
    }
    this.setDate();
  },
  properties: {
    office: null,
    forward: null,
    serviceType: {
      type: String,
      default: "office",
    },
  },
  methods: {
    setCurrentOffice() {
      const now = new Date();
      const hour = now.getHours();
      if (hour < 4) {
        this.office = this.currentServiceType == "family" ? "close_of_day_prayer" : "compline";
        this.forward = "yesterday";
        return;
      }
      if (hour >= 4 && hour < 11) {
        this.office = "morning_prayer";
        return;
      }
      if (hour >= 11 && hour < 15) {
        this.office = "midday_prayer";
        return;
      }
      if (hour >= 15 && hour < 20) {
        this.office = this.currentServiceType == "family" ? "early_evening_prayer" : "evening_prayer";
        return;
      }
      if (hour >= 20) {
        this.office = this.currentServiceType == "family" ? "close_of_day_prayer" : "compline";
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
            "morning_prayer",
            "evening_prayer",
            "midday_prayer",
            "compline",
            "early_evening_prayer",
            "close_of_day_prayer",
          ].includes(this.office)
      ) {
        this.notFound = true;
        return;
      }
      if (this.forward === "tomorrow") {
        today.setDate(today.getDate() + 1);
      }
      if (this.forward === "yesterday") {
        today.setDate(today.getDate() - 1);
      }
      this.calendarDate = today;
      this.key = `${this.office}-${this.calendarDate}`;
    },
  },
};
</script>
