<template>
  <div class="small-container home office">
    <Loading v-if="loading &&!notFound"/>
    <PageNotFound v-if="notFound"/>
    <div v-if="!loading && !error && !notFound" id="readings">

      <CalendarCard
          :calendar-date="calendarDate"
          :card="card"
      />
      <OfficeNav
          :calendar-date="calendarDate"
          selected-office="readings"
      />

      <h1>Readings</h1>

      <el-menu
          mode="horizontal"
          menu-trigger="click"
          unique-opened=true,
          :default-active="activeIndex"
      >
        <el-sub-menu index="1">
          <template #title>Daily Office</template>
          <el-menu-item
              v-for="value in daily_office" :key="value.name" class="full-width" :index="serviceLink(value.name)"
              @click="changeService(value.name)">{{
              value.name
            }}
          </el-menu-item>
          <div class="flex-grow"/>
        </el-sub-menu>
        <el-sub-menu index="2">
          <template #title>Holy Eucharist</template>
          <el-menu-item
              v-for="value in holy_eucharist" :key="value.name" class="full-width" :index="serviceLink(value.name)"
              @click="changeService(value.name)">{{
              value.name
            }}
          </el-menu-item>
        </el-sub-menu>

      </el-menu>

      <!--      <el-radio-group v-model="translation" class="ml-4 items-center">-->
      <!--        <el-radio label="esv" size="large">ESV</el-radio>-->
      <!--        <el-radio label="rsv" size="large">RSV</el-radio>-->
      <!--        <el-radio label="kjv" size="large">KJV</el-radio>-->
      <!--      </el-radio-group>-->
      <div class="mt-6">
        <h2 mt-2 pt-0>{{ service }}</h2>
        <CitationGroup
            v-for="(readings, number) in groupedReadings"
            :key="number" :readings="readings"
            @readingLinkClick="handleReadingLinkClick"/>
      </div>

      <Collects v-if="showCollects" :collects="collectsToShow"/>
      <Reading
          v-for="(reading, index) in readingsToShow" :id="readingName(index)" :key="index" :reading="reading"
          :psalm-cycle="psalmCycle" :length="reading.length" @cycle-60="setCycle60" @cycle-30="setCycle30"/>


    </div>
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
import PageNotFound from "@/views/PageNotFound";

export default {
  name: "Readings",
  components: {
    Loading,
    CalendarCard,
    OfficeNav,
    Reading,
    Collects,
    CitationGroup,
    PageNotFound,
  },
  props: {},
  data() {
    return {
      loading: true,
      error: false,
      calendarDate: null,
      card: null,
      services: null,
      daily_office: [],
      morning_prayer: [],
      evening_prayer: [],
      holy_eucharist: [],
      serviceLabels: null,
      service: null,
      readings: null,
      full: true,
      psalmCycle: "30",
      readingsToShow: [],
      translation: "esv",
      notFound: false,
      activeIndex: "1",
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
    // iterate through keys and values of this.services
    for (const [key, value] of Object.entries(this.services)) {
      if (value.type == "daily_office") {
        this.daily_office.push(value)
      } else if (value.type == "mass") {
        this.holy_eucharist.push(value)
      }
      if (key.includes("Morning Prayer")) {
        this.morning_prayer.push(value)
      } else if (key.includes("Evening Prayer")) {
        this.evening_prayer.push(value)
      }
    }
    this.serviceLabels = Object.keys(this.services)
    if (this.$route.params.service) {
      try {
        const service = this.$route.params.service.toLowerCase().replace("-", "_");
        const position = parseInt(this.$route.params.position || 0);
        if (service == "morning_prayer") {
          this.service = this.morning_prayer[position].name;
        } else if (service == "evening_prayer") {
          this.service = this.evening_prayer[position].name;
        } else if (service == "daily_office") {
          this.service = this.daily_office[position].name;
        } else if (service == "holy_eucharist") {
          this.service = this.holy_eucharist[position].name;
          this.activeIndex = "2"
        } else {
          this.service = this.morning_prayer[position].name
        }
      } catch (e) {
        this.notFound = true;
      }
    } else {
      this.service = this.morning_prayer[0].name
    }
    this.activeIndex = this.serviceLink(this.service)
    this.setReadingsToShow()
    this.error = false;
    this.loading = false;
  },
  methods: {
    readingID: function (reading) {
      const readingId = reading.citation.replace(/[\W_]+/g, "_")
      return `reading_${readingId}`.toLowerCase();
    },
    serviceLink: function (service) {
      let position = 0
      let service_name = ""
      if (service.includes("Morning Prayer")) {
        service_name = "morning_prayer"
        position = this.morning_prayer.findIndex(p => p.name == service);
      } else if (service.includes("Evening Prayer")) {
        service_name = "evening_prayer"
        position = this.evening_prayer.findIndex(p => p.name == service);
      } else {
        service_name = "holy_eucharist"
        position = this.holy_eucharist.findIndex(p => p.name == service);
      }
      let link = ""
      if (position > 0) {
        link = `/readings/${service_name}/${position}/${this.calendarDate.getFullYear()}/${
            this.calendarDate.getMonth() + 1
        }/${this.calendarDate.getDate()}`

      } else {
        link = `/readings/${service_name}/${this.calendarDate.getFullYear()}/${
            this.calendarDate.getMonth() + 1
        }/${this.calendarDate.getDate()}`

      }
      return link;
    },
    changeService: function (service) {
      console.log("WHAT", service)
      this.service = service
      const link = this.serviceLink(service)
      history.pushState(
          {},
          null,
          link
      )
      console.log("NEW SERVICE", this.service)
      this.setReadingsToShow()
    },
    setReadingsToShow: function () {
      if (this.service) {
        console.log("SERVICE", this.service)
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

h2 {
  font-size: 1.2rem;
  padding-top: 0 !important;
}

h3 {
  margin: 0 !important;
  padding: 0 0 1rem !important;
}

.el-select {
  margin-bottom: 2rem;
}


.collectsWrapper {
  padding: 1rem;
  border: 1px solid var(--font-color);
  border-radius: .25rem;
  margin: 1rem 0;
}

.flex-grow {
  flex-grow: 1;
}
</style>
