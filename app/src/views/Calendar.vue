<template>
  <h1>Calendar</h1>
  <Loading v-if="loading"/>
  <div class="full-width text-center">
    <el-switch
        v-model="includeMinorFeasts"
        size="large"
        active-text="Show All Feasts"
        inactive-text="Show Major Feasts Only"
        @change="updateIncludeMinorFeasts"
    />
  </div>
  <el-alert
      v-if="error" :title="error"
      type="error"
  />
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
    <template #date-cell="{ data }">
      <div
          class="dateCellWrapper" :class="getColorForDate(data.day)" @click="clickDateCell(data, $event)"
      >
        <p>{{ parseInt(data.day.split("-")[2]) }}</p>
        <p class="calendarText" v-html="getFeastNameForDate(data.day)"></p>
      </div>
    </template>
  </el-calendar>
</template>

<script>
// @ is an alias to /src

import {DynamicStorage} from "@/helpers/storage";
import {getURL} from "@/utils/request";

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
      includeMinorFeasts: false,
      error: null,
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
    updateIncludeMinorFeasts: async function () {
      const includeMinorFeasts = this.includeMinorFeasts ? "true" : "false"
      await DynamicStorage.setItem("includeMinorFeasts", includeMinorFeasts);
    },
    getColorForDate: function (day) {
      try {
        let commemorations = this.days[day].commemorations
        if (this.includeMinorFeasts) {
          commemorations = commemorations.filter((commemorations) => {
            return commemorations.rank.name.includes("FERIA") == false
          });
          if (!commemorations.length) {
            return this.days[day].season.colors[0]
          }
          return commemorations[0]['colors'][0]
        } else {
          if (this.days[day].major_feast) {
            return commemorations[0]['colors'][0]
          }
          return this.days[day].season.colors[0]
        }

      } catch {
        return ""
      }

    },
    getFeastNameForDate: function (day) {

      let feast = ""
      let bold = false;
      try {
        feast = this.days[day].major_feast
        if (feast) {
          bold = true;
        }
      } catch {
        feast = ""
      }
      if (this.includeMinorFeasts && !feast) {
        try {
          feast = this.days[day].major_or_minor_feast
        } catch {
          feast = ""
        }
      }
      if (bold) {
        return `<strong>${feast}</strong>`
      }
      return feast
    },
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
      const includeMinorFeasts = await DynamicStorage.getItem("includeMinorFeasts") || "false"
      this.includeMinorFeasts = includeMinorFeasts == "true"
      this.updateIncludeMinorFeasts()
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
        data = await getURL(
            `${process.env.VUE_APP_API_URL}api/v1/calendar/${this.year}-${this.month}`
        );
      } catch (e) {
        this.error =
            "There was an error retrieving the calendar. Please try again.";
        this.loading = false;
        return;
      }
      data.forEach((day) => {
        const dateString = day["date"];
        this.days[dateString] = day;
      });
      this.loading = false;
    },
    clickDateCell: async function (data, event) {
      event.preventDefault();
      event.stopPropagation();
      const day = data.day.split("-");
      await this.$router.push({
        name: `day`,
        params: {year: day[0], month: day[1], day: day[2]},
      });
      return;
    },
  },
};
</script>
<style lang="scss">

.dateCellWrapper {
  @media only screen and (max-width: 733px) {
    .calendarText {
      font-size: .4rem;
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
  @media only screen and (max-width: 733px) {
    padding: 3px;
  }
  height: 100%;
  width: 100%;
  margin-bottom: auto;
}

.el-calendar-table__row td {
  border: black 1px solid;
}


.red {

  background-color: #c21c13;
  color: white;

}

.green {

  background-color: #077339;
  color: white;

}

.white {

  background-color: white;
  color: black;

}

.purple {

  background-color: #64147d;
  color: white;

}

.black {

  background-color: black;
  color: white;

}

.rose {

  background-color: pink;
  color: black;

}

</style>
