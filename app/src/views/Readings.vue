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

      <FontSizer/>

      <h1>Readings</h1>

      <el-menu
          mode="horizontal"
          menu-trigger="click"
          unique-opened=true,
          :default-active="activeIndex"
          ellipsis=false,
      >
        <el-sub-menu index="1" ellipsis=false>
          <template #title>Office</template>
          <el-menu-item
              v-for="value in daily_office" :key="value.name" class="full-width" :index="serviceLink(value.name)"
              @click="changeService(value.name)">{{
              value.name
            }}
          </el-menu-item>
          <div class="flex-grow"/>
        </el-sub-menu>
        <el-sub-menu index="2" ellipsis=false>
          <template #title>Eucharist</template>
          <el-menu-item
              v-for="value in holy_eucharist" :key="value.name" class="full-width" :index="serviceLink(value.name)"
              @click="changeService(value.name)">{{
              value.name
            }}
          </el-menu-item>
        </el-sub-menu>

      </el-menu>

      <div class="flow-root">
        <div class="mt-1 sm:float-left">
          <el-radio-group
              v-model="psalmsTranslation" size="small"
              @change="changeTranslation()">
            <el-radio-button size="small" name="psalmsTranslation" label="contemporary">Contemporary Psalms
            </el-radio-button>
            <el-radio-button size="small" name="psalmsTranslation" label="traditional">Traditional Psalms
            </el-radio-button>
          </el-radio-group>
        </div>
        <div class="mt-1 sm:float-right">
          <el-radio-group v-model="translation" size="small" @change="changeTranslation()">
            <el-radio-button size="small" name="translation" label="esv">ESV</el-radio-button>
            <el-radio-button size="small" name="translation" label="kjv">KJV</el-radio-button>
            <el-radio-button size="small" name="translation" label="rsv">RSV</el-radio-button>

            <el-radio-button size="small" name="translation" label="nasb">NASB</el-radio-button>
            <el-radio-button size="small" name="translation" label="niv">NIV</el-radio-button>
            <el-radio-button size="small" name="translation" label="nrsvce">NRSV</el-radio-button>
            <el-radio-button size="small" name="translation" label="nabre">NAB-RE</el-radio-button>
          </el-radio-group>
        </div>

      </div>


      <Loading v-if="readingsLoading"/>
      <div id="main" class="readingsPanel" :v-if="!readingsLoading">
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
            :psalm-cycle="psalmCycle" :length="reading.length" :translation="translation"
            :psalms-translation="psalmsTranslation" @cycle-60="setCycle60"
            @cycle-30="setCycle30"/>
      </div>


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
import FontSizer from "@/components/FontSizer";
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
    FontSizer,
  },
  props: {},
  data() {
    return {
      loading: true,
      readingsLoading: false,
      error: false,
      calendarDate: null,
      card: null,
      services: null,
      daily_office: [],
      morning_prayer: [],
      evening_prayer: [],
      holy_eucharist: [],
      service: null,
      readings: null,
      full: true,
      psalmCycle: "30",
      readingsToShow: [],
      translation: "esv",
      psalmsTranslation: "contemporary",
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
    this.calendarDate = setCalendarDate(this.$route);
    let translation = localStorage.getItem('readings_translation');
    if (!translation) {
      const settings = this.$store.state.settings;
      translation = settings["bible_translation"];
    }
    localStorage.setItem('readings_translation', translation);
    this.translation = translation;

    let psalmsTranslation = localStorage.getItem('psalms_translation');
    if (!psalmsTranslation) {
      const settings = this.$store.state.settings;
      psalmsTranslation = settings["language_style"];
    }
    localStorage.setItem('psalms_translation', psalmsTranslation);
    this.psalmsTranslation = psalmsTranslation;

    await this.initialize();

  },
  methods: {
    initialize: async function () {
      this.readingsLoading = true;
      let data = null;
      try {
        const today_str =
            this.calendarDate.getFullYear() +
            "-" +
            (this.calendarDate.getMonth() + 1) +
            "-" +
            this.calendarDate.getDate();
        data = await this.$http.get(
            `${process.env.VUE_APP_API_URL}api/v1/readings/${today_str}?translation=${this.translation}&psalms=${this.psalmsTranslation}`
        );

      } catch (e) {
        this.error =
            "There was an error retrieving the office. Please try again.";
        this.loading = false;
        this.readingsLoading = false;
        return;
      }
      this.card = data.data.calendarDate
      this.services = data.data.services
      // iterate through keys and values of this.services
      this.morning_prayer = [];
      this.evening_prayer = [];
      this.daily_office = [];
      this.holy_eucharist = [];
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
      this.readingsLoading = false;
    },
    readingID: function (reading) {
      const readingId = reading.citation.replace(/[\W_]+/g, "_")
      return `reading_${readingId}`.toLowerCase();
    },
    changeTranslation: function () {
      localStorage.setItem('psalms_translation', this.psalmsTranslation);
      localStorage.setItem('readings_translation', this.translation);
      this.initialize();
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
      this.service = service
      const link = this.serviceLink(service)
      history.pushState(
          {},
          null,
          link
      )
      this.setReadingsToShow()
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
