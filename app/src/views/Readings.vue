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
    <el-select
        v-model="service"
        class="w-full"
        placeholder="Service"
        size="large"
        filterable
    >
      <el-option
          v-for="label in serviceLabels"
          :key="label"
          :label="label"
          :value="label"
      />
    </el-select>
    <h3>From Citations</h3>
    <CitationGroup
        v-for="(citationGroup, number) in citationGroupsToShow" :key="number"
        :citation-group="citationGroup"/>

    <h3>From readings</h3>
    <a
        v-for="(reading, index) in readingsToShow" :key="index" href="#" class="block"
        @click.prevent="goto(readingName(index))">{{
        reading.full.citation
      }}</a>
    <Collects v-if="showCollects" :collects="collectsToShow"/>
    <Reading
        v-for="(reading, index) in readingsToShow" :id="readingName(index)" :key="index" :reading="reading"
        :psalm-cycle="psalmCycle" @cycle-60="setCycle60" @cycle-30="setCycle30"/>


  </div>

</template>

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
<script>
// @ is an alias to /src
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
    };
  },
  computed: {
    readingsToShow: function () {
      if (this.service) {
        let serviceItems = this.services[this.service];
        return serviceItems['readings']
      }
      return [];
    },
    citationGroupsToShow: function () {
      if (this.service) {
        let serviceItems = this.services[this.service];
        console.log(serviceItems);
        if (serviceItems && serviceItems.citations) {
          console.log("CITATION", serviceItems.citations[1][0]);
          return serviceItems.citations;
        }

      }
      return [];
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
    this.error = false;
    this.loading = false;
  },
  methods: {
    readingName: function (index) {
      return `reading_${index}`;
    },
    collectName: function (index) {
      return `collect_${index}`;
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
