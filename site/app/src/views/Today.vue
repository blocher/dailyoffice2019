<template>
  <Office :office="office" :calendarDate="calendarDate" :key="key" />
</template>

<script>
// @ is an alias to /src
import Office from "@/views/Office";

export default {
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
    };
  },

  watch: {
    "$route.params.office": function () {
      this.setDate();
    },
    "$route.params.forward": function () {
      console.log("forward changed");
      this.setDate();
    },
  },
  async created() {
    this.setDate();
  },
  name: "Home",
  components: {
    Office,
  },
  properties: {
    office: null,
    forward: null,
  },
  methods: {
    setDate() {
      const today = new Date();
      this.office = this.$route.params.office;
      if (!this.office) {
        this.office = "morning_prayer";
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
