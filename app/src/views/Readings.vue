<template>
  <div class="small-container home office">
    <Loading v-if="loading"/>
    <div v-if="!loading && !error" id="readings">

      <CalendarCard
          :calendar-date="calendarDate"
          :card="card"
      />
      <OfficeNav
          :calendar-date="calendarDate"
          selected-office="readings"
      />
    </div>
    <h1>Readings</h1>

    <h3>{{ service }}</h3>
    <el-menu
        :default-active="activeIndex"
        mode="horizontal"
        menu-trigger="click"
    >
      <el-sub-menu index="1">
        <template #title>Daily Office</template>
        <el-menu-item class="full-width" index="/">Morning Prayer</el-menu-item>
        <el-menu-item class="full-width" index="/">Evening Prayer</el-menu-item>
      </el-sub-menu>
      <el-sub-menu index="2">
        <template #title>Holy Eucharist</template>
        <el-menu-item class="full-width" index="/">Primary Service</el-menu-item>
      </el-sub-menu>
    </el-menu>
    <el-select
        v-model="service"
        class="w-full"
        placeholder="Service"
        size="large"
        filterable
        @change="setReadingsToShow"
    >
      <el-option
          v-for="label in serviceLabels"
          :key="label"
          :label="label"
          :value="label"
      />
    </el-select>
    <CitationGroup
        v-for="(readings, number) in groupedReadings"
        :key="number" :readings="readings"
        @readingLinkClick="handleReadingLinkClick"/>


    <Collects v-if="showCollects" :collects="collectsToShow"/>
    <Reading
        v-for="(reading, index) in readingsToShow" :id="readingName(index)" :key="index" :reading="reading"
        :psalm-cycle="psalmCycle" :length="reading.length" @cycle-60="setCycle60" @cycle-30="setCycle30"/>


  </div>

</template>

<script>
// @ is an alias to /src
import {nextTick} from 'vue'
import Loading from "@/components/Loading";
import setCalendarDate from "@/helpers/setCalendarDate";
import CalendarCard from "@/components/CalendarCard";
import OfficeNav from "@/components/OfficeNav";
import Reading from "@/components/Reading";
import Collects from "@/components/Collects";
import CitationGroup from "@/components/CitationGroup";

export default {
  name: "Readings",
  components: {
    Loading,
    CalendarCard,
    OfficeNav,
    Reading,
    Collects,
    CitationGroup,
  },
  props: {},
  data() {
    return {
      loading: true,
      error: false,
      calendarDate: null,
      card: null,
      services: null,
      serviceLabels: null,
      service: null,
      readings: null,
      full: true,
      psalmCycle: "30",
      readingsToShow: [],
    };
  },
  computed: {
    groupedReadings: function () {
      const groups = {}
      this.readingsToShow.forEach(reading => {
        if (reading.full.reading_number in groups) {
          groups[reading.full.reading_number].push(reading)
        } else {
          groups[reading.full.reading_number] = [reading]
        }
      });
      return groups;
    },
    collectsToShow: function () {
      if (this.service) {
        let serviceItems = this.services[this.service];
        let collects = serviceItems['collects']
        collects = collects.map(collect => {
          return collect.replace(" Amen.", "")
        });
        return collects
      }
      return [];
    },
    showCollects: function () {
      return this.collectsToShow.length > 0
    },
  },
  async created() {
    let data = null;
    this.calendarDate = setCalendarDate(this.$route);
    try {
      const today_str =
          this.calendarDate.getFullYear() +
          "-" +
          (this.calendarDate.getMonth() + 1) +
          "-" +
          this.calendarDate.getDate();
      data = await this.$http.get(
          `${process.env.VUE_APP_API_URL}api/v1/readings/` +
          today_str
      );
    } catch (e) {
      this.error =
          "There was an error retrieving the office. Please try again.";
      this.loading = false;
      return;
    }
    this.card = data.data.calendarDate
    this.services = data.data.services
    this.serviceLabels = Object.keys(this.services)
    this.service = this.serviceLabels[0]
    this.setReadingsToShow()
    this.error = false;
    this.loading = false;
  },
  methods: {
    readingID: function (reading) {
      const readingId = reading.citation.replace(/[\W_]+/g, "_")
      return `reading_${readingId}`.toLowerCase();
    },
    setReadingsToShow: function () {
      if (this.service) {
        let serviceItems = this.services[this.service];
        this.readingsToShow = serviceItems['readings'].map((reading) => {
          return reading;
        })
        return;
      }
      this.readingsToShow = [];
    },
    handleReadingLinkClick: async function (data) {
      this.readingsToShow = this.readingsToShow.map((reading) => {
        if (reading.full.citation == data.reading.citation && data.length == "full") {
          reading.length = data.length
        }
        if (reading.abbreviated.citation == data.reading.citation && data.length == "abbreviated") {
          reading.length = data.length
        }
        return reading;
      })
      if (data.reading.cycle == "60") {
        this.setCycle60()
      }
      if (data.reading.cycle == "30") {
        this.setCycle30()
      }
      await nextTick();
      this.goto(this.readingID(data.reading))
    },
    readingName: function (index) {
      return `reading_${index}`;
    },
    goto(id) {
      const menu = document.getElementById('topMenu')
      const menuHeight = menu ? menu.offsetHeight : 0
      const element = document.getElementById(id);
      const top = element.offsetTop;
      window.scrollTo({
        top: top - menuHeight - 5,
        left: 0,
        behavior: 'smooth'
      });
    },
    setCycle30: function () {
      this.psalmCycle = "30";
    },
    setCycle60: function () {
      this.psalmCycle = "60";
    },
  },

};
</script>
<style scoped lang="scss">
h1 {
  margin: 2rem 0 0 !important;
}

h3 {
  margin: 0 !important;
  padding: 0 0 1rem !important;
}

.el-select {
  margin-bottom: 2rem;
}
</style>
