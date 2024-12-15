<template>
  <div class="small-container home office">
    <Loading v-if="loading && !notFound" />
    <PageNotFound v-if="notFound" />
    <el-alert v-if="error" :title="error" type="error" />
    <div v-if="!loading && !notFound" id="readings">
      <CalendarCard
        v-if="!error"
        :calendar-date="calendarDate"
        :card="card"
        service-type="readings"
        office="readings"
      />
      <OfficeNav :calendar-date="calendarDate" selected-office="readings" />

      <h1>Readings</h1>

      <el-divider />

      <el-row class="mt-2 content-stretch">
        <el-col :span="24">
          <h4 class="text-left mt-4">Daily Offices</h4>
          <div v-for="service in dailyOfficeData" :key="service.name">
            <div class="grid grid-cols-12 gap-3 even:bg-grey mb-5">
              <div class="m-auto">
                <font-awesome-icon
                  v-if="service.active"
                  :icon="['fad', 'fa-octagon-check']"
                />
              </div>
              <div class="col-span-11">
                <span v-if="service.active" v-html="service.name"></span>
                <span v-if="!service.active"
                  ><a
                    :href="serviceLink(service.name)"
                    @click.prevent="changeService(service.name)"
                    v-html="service.name"
                  ></a
                ></span>
              </div>
            </div>
          </div>

          <h4 class="text-left mt-4">Holy Eucharist</h4>
          <div v-for="service in eucharistData" :key="service.name">
            <div class="grid grid-cols-12 gap-3 even:bg-grey mb-5">
              <div class="m-auto">
                <font-awesome-icon
                  v-if="service.active"
                  :icon="['fad', 'fa-octagon-check']"
                />
              </div>
              <div class="col-span-11">
                <span v-if="service.active" v-html="service.name"></span>
                <span v-if="!service.active"
                  ><a
                    :href="serviceLink(service.name)"
                    @click.prevent="changeService(service.name)"
                    v-html="service.name"
                  ></a
                ></span>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>

      <el-divider />

      <el-row>
        <el-col :span="24">
          <h4>Psalter Version</h4>
          <el-select
            v-model="psalmsTranslation"
            class="mx-1 mb-4 full-width"
            placeholder="Select"
            size="large"
            @change="changeTranslation()"
          >
            <el-option
              v-for="item in psalmsTranslations"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-col>
      </el-row>
      <el-row>
        <el-col :span="24">
          <h4>Translation</h4>
          <el-select
            v-model="translation"
            class="mx-1 mb-4 full-width"
            placeholder="Select"
            size="large"
            @change="changeTranslation()"
          >
            <el-option
              v-for="item in translations"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-col>
      </el-row>
      <el-row>
        <el-col :span="24">
          <h4>Psalm Recitation Style</h4>
          <el-select
            v-model="psalmStyle"
            class="mx-1 mb-4 full-width"
            placeholder="Select"
            size="large"
            @change="changeStyle()"
          >
            <el-option
              v-for="item in psalmStyles"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-col>
      </el-row>

      <div class="flow-root">
        <!--        <div class="mt-1 sm:float-left">-->
        <!--          <el-radio-group-->
        <!--              v-model="psalmsTranslation" size="small"-->
        <!--              @change="changeTranslation()">-->
        <!--            <el-radio-button size="small" name="psalmsTranslation" label="contemporary">Contemporary Psalms-->
        <!--            </el-radio-button>-->
        <!--            <el-radio-button size="small" name="psalmsTranslation" label="traditional">Traditional Psalms-->
        <!--            </el-radio-button>-->
        <!--          </el-radio-group>-->
        <!--        </div>-->
        <!--        <div class="mt-1 sm:float-right">-->
        <!--          <el-radio-group v-model="translation" size="small" @change="changeTranslation()">-->
        <!--            <el-radio-button size="small" name="translation" label="esv">ESV</el-radio-button>-->
        <!--            <el-radio-button size="small" name="translation" label="kjv">KJV</el-radio-button>-->
        <!--            <el-radio-button size="small" name="translation" label="rsv">RSV</el-radio-button>-->

        <!--            <el-radio-button size="small" name="translation" label="nasb">NASB</el-radio-button>-->
        <!--            <el-radio-button size="small" name="translation" label="niv">NIV</el-radio-button>-->
        <!--            <el-radio-button size="small" name="translation" label="nrsvce">NRSV</el-radio-button>-->
        <!--            <el-radio-button size="small" name="translation" label="nabre">NAB-RE</el-radio-button>-->
        <!--          </el-radio-group>-->
        <!--        </div>-->
      </div>
      <Loading v-if="readingsLoading" />
      <FontSizer />
    </div>
  </div>
  <div id="main" class="readingsPanel" :v-if="!readingsLoading">
    <div class="mt-6">
      <h2 mt-2 pt-0>{{ service }}</h2>
      <CitationGroup
        v-for="(readings, number) in groupedReadings"
        :key="number"
        :readings="readings"
        @reading-link-click="handleReadingLinkClick"
      />
    </div>

    <Collects
      v-if="showCollects"
      :collects="collectsToShow"
      :style="'Contemporary'"
    />
    <Collects
      v-if="showTraditionalCollects"
      :collects="traditionalCollectsToShow"
      :style="'Traditional'"
    />
    <Reading
      v-for="(reading, index) in readingsToShow"
      :id="readingName(index)"
      :key="index"
      :reading="reading"
      :psalm-cycle="psalmCycle"
      :length="reading.length"
      :translation="translation"
      :psalms-translation="psalmsTranslation"
      @cycle-60="setCycle60"
      @cycle-30="setCycle30"
    />
  </div>
</template>

<script>
// @ is an alias to /src
import { nextTick } from "vue";
import Loading from "@/components/Loading.vue";
import setCalendarDate from "@/helpers/setCalendarDate";
import CalendarCard from "@/components/CalendarCard.vue";
import OfficeNav from "@/components/OfficeNav.vue";
import Reading from "@/components/Reading.vue";
import Collects from "@/components/Collects.vue";
import CitationGroup from "@/components/CitationGroup.vue";
import FontSizer from "@/components/FontSizer.vue";
import PageNotFound from "@/views/PageNotFound.vue";
import { DynamicStorage } from "@/helpers/storage";

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
      translations: [
        { value: "esv", label: "ESV: English Standard Version" },
        { value: "kjv", label: "KJV: King James Version" },
        { value: "rsv", label: "RSV: Revised Standard Version" },
        { value: "nasb", label: "NASB: New American Standard Bible" },
        { value: "niv", label: "NIV: New International Version" },
        { value: "nrsvce", label: "NRSV: New Revised Standard Version" },
        { value: "nabre", label: "NAB-RE: New American Bible Revised Edition" },
      ],
      psalmsTranslation: "contemporary",
      psalmsTranslations: [
        {
          label: "Contemporary Psalms",
          value: "contemporary",
        },
        {
          label: "Traditional Psalms",
          value: "traditional",
        },
      ],
      psalmStyle: "whole_verse",
      psalmStyles: [
        {
          label: "Antiphonally by Whole Verse",
          value: "whole_verse",
        },
        {
          label: "Antiphonally by Half Verse",
          value: "half_verse",
        },
        {
          label: "In Unison",
          value: "unison",
        },
      ],
      notFound: false,
      activeIndex: "1",
      uniqueOpened: true,
      ellipsis: false,
    };
  },
  computed: {
    dailyOfficeData: function () {
      return this.daily_office.map((service) => {
        return {
          active: service.name === this.service,
          name: service.name,
        };
      });
    },
    eucharistData: function () {
      return this.holy_eucharist.map((service) => {
        return {
          active: service.name === this.service,
          name: service.name,
        };
      });
    },
    groupedReadings: function () {
      const groups = {};
      this.readingsToShow.forEach((reading) => {
        if (reading.full.reading_number in groups) {
          groups[reading.full.reading_number].push(reading);
        } else {
          groups[reading.full.reading_number] = [reading];
        }
      });
      return groups;
    },
    collectsToShow: function () {
      if (this.service) {
        let serviceItems = this.services[this.service];
        let collects = serviceItems["collects"];
        collects = collects.map((collect) => {
          return collect.replace(" Amen.", "");
        });
        return collects;
      }
      return [];
    },
    showCollects: function () {
      return this.collectsToShow.length > 0;
    },
    traditionalCollectsToShow: function () {
      if (this.service) {
        let serviceItems = this.services[this.service];
        let collects = [];
        try {
          collects = serviceItems["traditional_collects"];
        } catch (e) {
          return [];
        }
        collects = collects.map((collect) => {
          return collect.replace(" Amen.", "");
        });
        return collects;
      }
      return [];
    },
    showTraditionalCollects: function () {
      return this.traditionalCollectsToShow.length > 0;
    },
  },
  async created() {
    this.calendarDate = setCalendarDate(this.$route);

    let translation = await DynamicStorage.getItem("readings_translation");
    if (!translation) {
      const settings = this.$store.state.settings;
      translation = settings["bible_translation"];
    }
    await DynamicStorage.setItem("readings_translation", translation);
    this.translation = translation;

    let psalmsTranslation = await DynamicStorage.getItem("psalms_translation");
    if (!psalmsTranslation) {
      const settings = this.$store.state.settings;
      psalmsTranslation = settings["language_style"];
    }
    await DynamicStorage.setItem("psalms_translation", psalmsTranslation);
    this.psalmsTranslation = psalmsTranslation;

    let psalmCycle = await DynamicStorage.getItem("psalter");
    if (!psalmCycle) {
      const settings = this.$store.state.settings;
      psalmCycle = settings["psalter"];
    }
    await DynamicStorage.setItem("psalter", psalmCycle);
    this.psalmCycle = psalmCycle;

    let psalmStyle = await DynamicStorage.getItem("psalm_style");
    if (!psalmStyle) {
      const settings = this.$store.state.settings;
      psalmStyle = settings["psalm_style"];
    }
    await DynamicStorage.setItem("psalm_style", psalmStyle);
    this.psalmStyle = psalmStyle;

    await this.initialize();
  },
  methods: {
    initialize: async function () {
      this.readingsLoading = true;
      let data = null;
      try {
        this.availableSettings = await this.$store.state.availableSettings;
        await this.$store.dispatch("initializeSettings");
        const settings = await this.$store.state.settings;
        const queryString = Object.keys(settings)
          .map((key) => key + "=" + settings[key])
          .join("&");

        const today_str =
          this.calendarDate.getFullYear() +
          "-" +
          (this.calendarDate.getMonth() + 1) +
          "-" +
          this.calendarDate.getDate();
        data = await this.$http.get(
          `${import.meta.env.VUE_APP_API_URL}api/v1/readings/${today_str}?translation=${this.translation}&psalms=${this.psalmsTranslation}&style=${this.psalmStyle}&` +
            queryString,
        );
      } catch (e) {
        this.error =
          "There was an error retrieving the readings. Please try again.";
        this.loading = false;
        this.readingsLoading = false;
        return;
      }
      this.card = data.data.calendarDate;
      this.services = data.data.services;
      // iterate through keys and values of this.services
      this.morning_prayer = [];
      this.evening_prayer = [];
      this.daily_office = [];
      this.holy_eucharist = [];
      for (const [key, value] of Object.entries(this.services)) {
        if (value.type == "daily_office") {
          this.daily_office.push(value);
        } else if (value.type == "mass") {
          this.holy_eucharist.push(value);
        }
        if (key.includes("Morning Prayer")) {
          this.morning_prayer.push(value);
        } else if (key.includes("Evening Prayer")) {
          this.evening_prayer.push(value);
        }
      }
      if (this.$route.params.service) {
        try {
          const service = this.$route.params.service
            .toLowerCase()
            .replace("-", "_");
          const position = parseInt(this.$route.params.position || 0);
          if (service == "morning_prayer") {
            this.service = this.morning_prayer[position].name;
          } else if (service == "evening_prayer") {
            this.service = this.evening_prayer[position].name;
          } else if (service == "daily_office") {
            this.service = this.daily_office[position].name;
          } else if (service == "holy_eucharist") {
            this.service = this.holy_eucharist[position].name;
            this.activeIndex = "2";
          } else {
            this.service = this.morning_prayer[position].name;
          }
        } catch (e) {
          this.notFound = true;
        }
      } else {
        this.service = this.morning_prayer[0].name;
      }
      this.activeIndex = this.serviceLink(this.service);
      this.setReadingsToShow();
      this.error = false;
      this.loading = false;
      this.readingsLoading = false;
    },
    readingID: function (reading) {
      const readingId = reading.citation.replace(/[\W_]+/g, "_");
      return `reading_${readingId}`.toLowerCase();
    },
    changeTranslation: async function () {
      await DynamicStorage.setItem(
        "psalms_translation",
        this.psalmsTranslation,
      );
      await DynamicStorage.setItem("readings_translation", this.translation);
      this.initialize();
    },
    changeStyle: async function () {
      await DynamicStorage.setItem("psalm_style", this.psalmStyle);
      this.initialize();
    },
    serviceLink: function (service) {
      let serviceValues = this.getPositionAndServiceName(service);
      let link = "";
      if (serviceValues.position > 0) {
        link = `/readings/${serviceValues.service_name}/${serviceValues.position}/${this.calendarDate.getFullYear()}/${
          this.calendarDate.getMonth() + 1
        }/${this.calendarDate.getDate()}`;
      } else {
        link = `/readings/${serviceValues.service_name}/${this.calendarDate.getFullYear()}/${
          this.calendarDate.getMonth() + 1
        }/${this.calendarDate.getDate()}`;
      }
      return link;
    },
    getPositionAndServiceName: function (service) {
      let position = 0;
      let service_name = "";
      if (service.includes("Morning Prayer")) {
        service_name = "morning_prayer";
        position = this.morning_prayer.findIndex((p) => p.name == service);
      } else if (service.includes("Evening Prayer")) {
        service_name = "evening_prayer";
        position = this.evening_prayer.findIndex((p) => p.name == service);
      } else {
        service_name = "holy_eucharist";
        position = this.holy_eucharist.findIndex((p) => p.name == service);
      }
      return { position: position, service_name: service_name };
    },
    changeService: function (service) {
      this.service = service;
      let serviceValues = this.getPositionAndServiceName(service);
      let routeName = "readingsByServiceAndDate";
      if (serviceValues.position > 0) {
        routeName = "readingsByServicePositionAndDate";
      }
      this.$router.push({
        name: routeName,
        params: {
          service: serviceValues.service_name,
          year: this.$route.params.year,
          month: this.$route.params.month,
          day: this.$route.params.day,
          position: serviceValues.position,
        },
      });
      this.setReadingsToShow();
    },
    setReadingsToShow: function () {
      if (this.service) {
        let serviceItems = this.services[this.service];
        this.readingsToShow = serviceItems["readings"].map((reading) => {
          return reading;
        });
        return;
      }
      this.readingsToShow = [];
    },
    handleReadingLinkClick: async function (data) {
      this.readingsToShow = this.readingsToShow.map((reading) => {
        if (
          reading.full.citation == data.reading.citation &&
          data.length == "full"
        ) {
          reading.length = data.length;
        }
        if (
          reading.abbreviated.citation == data.reading.citation &&
          data.length == "abbreviated"
        ) {
          reading.length = data.length;
        }
        return reading;
      });
      if (data.reading.cycle == "60") {
        this.setCycle60();
      }
      if (data.reading.cycle == "30") {
        this.setCycle30();
      }
      await nextTick();
      this.goto(this.readingID(data.reading));
    },
    readingName: function (index) {
      return `reading_${index}`;
    },
    goto(id) {
      const menu = document.getElementById("topMenu");
      const menuHeight = menu ? menu.offsetHeight : 0;
      const element = document.getElementById(id);
      const top = element.offsetTop;
      window.scrollTo({
        top: top - menuHeight - 5,
        left: 0,
        behavior: "smooth",
      });
    },
    setCycle30: async function () {
      this.psalmCycle = "30";
      await DynamicStorage.setItem("psalter", this.psalmCycle);
    },
    setCycle60: async function () {
      this.psalmCycle = "60";
      await DynamicStorage.setItem("psalter", this.psalmCycle);
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
  width: 100%;
}

.collectsWrapper {
  padding: 1rem;
  border: 1px solid var(--font-color);
  border-radius: 0.25rem;
  margin: 1rem 0;
}

.flex-grow {
  flex-grow: 1;
}
</style>
