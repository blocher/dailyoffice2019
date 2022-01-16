<template>
  <Office :office="office" :calendarDate="calendarDate" />
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
    };
  },
  async created() {
    const today = new Date();
    this.office = "morning";
    this.calendarDate = today;
  },
  name: "Home",
  components: {
    Office,
  },
};
</script>
