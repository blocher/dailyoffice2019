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
      calendarDate: null,
    };
  },
  async created() {
    this.office = "morning_prayer";

    const yyyy = parseInt(this.$route.params.year);
    const mm = parseInt(this.$route.params.month);
    const dd = parseInt(this.$route.params.day);
    const calendarDate = new Date(yyyy, mm - 1, dd);
    const valid_date =
      calendarDate instanceof Date &&
      !isNaN(calendarDate) &&
      !isNaN(calendarDate.getTime());
    if (!valid_date) {
      await this.$router.push({ name: "not_found" });
      return;
    }

    this.calendarDate = calendarDate;
  },
  name: "Today",
  components: {
    Office,
  },
};
</script>
