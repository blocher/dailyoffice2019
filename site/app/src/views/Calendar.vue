<template>
  <h1>Calendar</h1>
  <Loading v-if="loading"/>
  <el-calendar v-model="date" v-if="!loading">
    <template #header="{ date }">
      <span>{{ date }}</span>


      <el-button-group>
        <!--        <el-button size="small" @click="selectDate('prev-year')"-->
        <!--          >Previous Year</el-button-->
        <!--        >-->

        <el-button size="small" @click="selectDate('today')">Now</el-button>
        <el-button size="small" @click="selectDate('prev-month')"
        >Previous Month
        </el-button>
        <el-button size="small" @click="selectDate('next-month')"
        >Next Month
        </el-button>
        <!--        <el-button size="small" @click="selectDate('next-year')"-->
        <!--          >Next Year</el-button-->
        <!--        >-->
      </el-button-group>
    </template>
    <template #dateCell="{ data }">
      <div class="dateCellWrapper" v-on:click="clickDateCell(data)">
        <p>{{ parseInt(data.day.split("-")[2]) }}</p>
        <p>
          <small v-html="days[data.day]"></small>
        </p>
      </div>
    </template>
  </el-calendar>
</template>

<style lang="scss">
td {
  height: 1px !important;
}

.el-calendar-day {
  min-height: 75px;
  height: 100% !important;
  padding: 0 !important;
  display: flex;
  margin-bottom: auto;

  p {
    line-height: 1.1rem;
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
  name: "Calendar",
  components: {},
  methods: {
    selectDate: async function (changeType) {
      if (changeType == "prev-month") {
        if (this.month == 1) {
          this.year = this.year - 1
          this.month = 12
        } else {
          this.month = this.month - 1
        }
      }
      if (changeType == "next-month") {
        if (this.month == 12) {
          this.year = this.year + 1
          this.month = 1
        } else {
          this.month = this.month + 1
        }
      }
      if (changeType == "today") {
        const today = new Date()
        this.year = today.getFullYear()
        this.month = today.getMonth() + 1
      }
      const year = this.year
      const month = this.month
      await this.$router.push({name: "calendar", params: {year, month}});
      return;
    },
    setCalendar: async function () {
      this.loading = true;
      let data = null;
      this.year = parseInt(this.$route.params.year);
      this.month = parseInt(this.$route.params.month);
      this.date = new Date(this.year, this.month - 1, 1);
      try {
        data = await this.$http.get(
            `http://127.0.0.1:8000/api/v1/calendar/${this.$route.params.year}-${this.$route.params.month}`
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
    clickDateCell: function (data) {
      alert("clicked");
      console.log(data);
    },

  },
};
</script>
