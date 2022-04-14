<template>
  <h1>Calendar</h1>
  <Loading v-if="loading"/>
  <el-calendar
      v-if="!loading" v-model="date"
  >
    <template #header="{ date }">
      <span>{{ date }}</span>

      <el-button-group>
        <!--        <el-button size="small" @click="selectDate('prev-year')"-->
        <!--          >Previous Year</el-button-->
        <!--        >-->

        <el-button
            size="small" @click="selectDate('today')"> Now
        </el-button>
        <el-button
            size="small" @click="selectDate('prev-month')"
        >
          Previous Month
        </el-button>
        <el-button
            size="small" @click="selectDate('next-month')"
        >
          Next Month
        </el-button>
        <!--        <el-button size="small" @click="selectDate('next-year')"-->
        <!--          >Next Year</el-button-->
        <!--        >-->
      </el-button-group>
    </template>
    <template #dateCell="{ data }">
      <div
          class="dateCellWrapper" @click="clickDateCell(data, $event)"
      >
        <p>{{ parseInt(data.day.split("-")[2]) }}</p>
        <p class="calendarText" v-html="days[data.day]"></p>
      </div>
    </template>
  </el-calendar>
</template>

<style lang="scss">

.dateCellWrapper {
  @media only screen and (max-width: 733px) {
    .calendarText {
      font-size: .5rem;
    }
  }
}

td {
  height: 1px !important;
}

.el-calendar,
.el-calendar-table td.is-selected {
  background-color: var(--background-color) !important;
}

.el-calendar-day {
  min-height: 75px;
  height: 100% !important;
  padding: 0 !important;
  display: flex;
  margin-bottom: auto;
  color: var(--el-text-color-primary);

  &:hover {
    color: var(--font-on-white-background);
  }

  p {
    line-height: 1.1em;
  }
}

.dateCellWrapper {
  padding: 8px;
  height: 100%;
  width: 100%;
  margin-bottom: auto;
}
</style>
<script>
// @ is an alias to /src

export default {
  name: "Calendar",
  components: {},
  data() {
    return {
      year: null,
      month: null,
      days: {},
      date: null,
      loading: true,
    };
  },
  watch: {
    "$route.params.year": function () {
      this.setCalendar();
    },
    "$route.params.month": function () {
      this.setCalendar();
    },
  },
  async created() {
    this.setCalendar();
  },
  methods: {
    selectDate: async function (changeType) {
      if (changeType == "prev-month") {
        if (this.month == 1) {
          this.year = this.year - 1;
          this.month = 12;
        } else {
          this.month = this.month - 1;
        }
      }
      if (changeType == "next-month") {
        if (this.month == 12) {
          this.year = this.year + 1;
          this.month = 1;
        } else {
          this.month = this.month + 1;
        }
      }
      if (changeType == "today") {
        const today = new Date();
        this.year = today.getFullYear();
        this.month = today.getMonth() + 1;
      }
      const year = this.year;
      const month = this.month;
      await this.$router.push({name: "calendar", params: {year, month}});
      return;
    },
    setCalendar: async function () {
      this.loading = true;
      let data = null;
      const today = new Date();
      let year = parseInt(this.$route.params.year);
      let month = parseInt(this.$route.params.month);
      if (!year) {
        year = today.getFullYear();
        month = today.getMonth() + 1;
      } else if (!month) {
        month = 1;
      }
      this.year = year;
      this.month = month;
      this.date = new Date(this.year, this.month - 1, 1);
      try {
        data = await this.$http.get(
            `${process.env.VUE_APP_API_URL}api/v1/calendar/${this.year}-${this.month}`
        );
      } catch (e) {
        this.error =
            "There was an error retrieving the office. Please try again.";
        this.loading = false;
        return;
      }
      data.data.forEach((day) => {
        const dateString = day["date"];
        this.days[dateString] = day["major_feast"];
      });
      this.loading = false;
    },
    clickDateCell: async function (data, event) {
      event.preventDefault();
      event.stopPropagation();
      const day = data.day.split("-");
      console.log(window.history, "1", day);
      await this.$router.push({
        name: `day`,
        params: {year: day[0], month: day[1], day: day[2]},
      });
      console.log(window.history, "2");
      return;
    },
  },
};
</script>
