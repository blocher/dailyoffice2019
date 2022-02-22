<template>
  <Office :office="office" :calendar-date="calendarDate" />
</template>

<script>
// @ is an alias to /src
import Office from "@/views/Office";
import setCalendarDate from "@/helpers/setCalendarDate";

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
      calendarDate: null,
    };
  },
  async created() {
    this.office = this.$route.params.office;

    this.calendarDate = setCalendarDate(this.$route);
    if (!this.calendarDate) {
      await this.$router.push({
        name: "not_found",
        params: { pathMatch: this.$route.path.split("/").slice(1) },
      });
      return;
    }
  },
};
</script>
