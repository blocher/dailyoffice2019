<template>
  <Office :key="key" :office="office" :calendar-date="calendarDate" />
</template>

<script>
// @ is an alias to /src
import Office from "@/views/Office";

export default {
  name: "Today",
  components: {
    Office,
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
    this.setDate();
  },
  properties: {
    office: null,
    forward: null,
  },
  methods: {
    async setDate() {
      const today = new Date();
      this.office = this.$route.params.office;
      if (!this.office) {
        this.office = "morning_prayer";
      }
      if (
        ![
          "morning_prayer",
          "evening_prayer",
          "midday_prayer",
          "compline",
        ].includes(this.office)
      ) {
        await this.$router.push({
          name: "not_found",
          params: { pathMatch: this.$route.path.split("/").slice(1) },
        });
        return;
      }
      if (this.$route.params.forward === "tomorrow") {
        today.setDate(today.getDate() + 1);
      }
      if (this.$route.params.forward === "yesterday") {
        today.setDate(today.getDate() - 1);
      }
      this.calendarDate = today;
      this.key = `${this.office}-${this.calendarDate}`;
    },
  },
};
</script>
