<template>
  <div class="small-container home office">
    <PageNotFound v-if="notFound"/>
    <div v-if="!notFound">
      <Loading v-if="loading"/>


      <CalendarCard
          v-if="!loading"
          :office="office"
          :calendar-date="calendarDate"
          :card="card"
          :service-type="serviceType"
      />
      <el-alert
          v-if="error" :title="error"
          type="error"
      />
      <OfficeNav
          :calendar-date="calendarDate"
          :selected-office="office"
          :service-type="serviceType"
      />

      <div class="font-size-block my-2">
        <div class="w-1/6 inline-block">
          <font-awesome-icon
              :icon="['fad', 'font-case']" size="sm"
          />
        </div>
        <div class="w-2/3 inline-block">
          <el-slider
              v-model="fontSize"
              class="w-3/4"
              :min="sliderMin"
              :max="sliderMax"
              :format-tooltip="displayFontSize"
              @input="setFontSize"
          />
        </div>
        <div class="w-1/6 inline-block text-right">
          <font-awesome-icon
              :icon="['fad', 'font-case']" size="lg"
          />
        </div>
      </div>

      <div id="office">
        <div
            v-for="module in modules" :key="module.name"
        >
          <div
              v-for="line in module.lines" :key="line.content"
          >
            <OfficeHeading
                v-if="line.line_type == 'heading'" :line="line"
            />
            <OfficeSubheading
                v-if="line.line_type == 'subheading'"
                :line="line"
            />
            <OfficeCitation
                v-if="line.line_type == 'citation'" :line="line"
            />
            <OfficeHTML
                v-if="line.line_type == 'html'" :line="line"
            />
            <OfficeLeader
                v-if="line.line_type == 'leader'" :line="line"
            />
            <OfficeLeaderDialogue
                v-if="line.line_type == 'leader_dialogue'"
                :line="line"
            />
            <OfficeCongregation
                v-if="line.line_type == 'congregation'"
                :line="line"
            />
            <OfficeCongregationDialogue
                v-if="line.line_type == 'congregation_dialogue'"
                :line="line"
            />

            <OfficeRubric
                v-if="line.line_type == 'rubric'" :line="line"
            />
            <OfficeSpacer v-if="line.line_type == 'spacer'"/>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.el-alert {
  margin-top: 2em;
}
</style>

<script>
// @ is an alias to /src
import OfficeHeading from "@/components/OfficeHeading";
import OfficeSubheading from "@/components/OfficeSubheading";
import OfficeCitation from "@/components/OfficeCitation";
import OfficeHTML from "@/components/OfficeHTML";
import OfficeCongregation from "@/components/OfficeCongregation";
import OfficeLeader from "@/components/OfficeLeader";
import OfficeCongregationDialogue from "@/components/OfficeCongregationDialogue";
import OfficeLeaderDialogue from "@/components/OfficeLeaderDialogue";
import OfficeRubric from "@/components/OfficeRubric";
import OfficeSpacer from "@/components/OfficeSpacer";
import Loading from "@/components/Loading";
import CalendarCard from "@/components/CalendarCard";
import OfficeNav from "@/components/OfficeNav";
import PageNotFound from "@/views/PageNotFound";

export default {
  name: "Office",
  components: {
    OfficeHeading,
    OfficeSubheading,
    OfficeCitation,
    OfficeHTML,
    OfficeCongregation,
    OfficeLeader,
    OfficeCongregationDialogue,
    OfficeLeaderDialogue,
    OfficeRubric,
    OfficeSpacer,
    Loading,
    CalendarCard,
    OfficeNav,
    PageNotFound,
  },
  props: {
    office: {
      type: String,
    },
    calendarDate: {
      type: Date,
    },
    serviceType: {
      default: "office",
      type: String,
    },
  },
  data() {
    return {
      counter: 0,
      modules: null,
      loading: true,
      error: false,
      card: "",
      fontSize: 20,
      sliderMin: 10,
      sliderMax: 40,
      notFound: false,
    };
  },
  mounted() {
    if (localStorage.fontSize) {
      this.fontSize = parseInt(localStorage.fontSize);
    } else {
      localStorage.fontSize = this.fontSize;
    }
    this.setFontSize(this.fontSize);
    localStorage.setItem("serviceType", this.serviceType);
  },

  async created() {
    const valid_daily_offices = [
      "morning_prayer",
      "midday_prayer",
      "evening_prayer",
      "compline",
    ];
    const valid_family_offices = [
      "morning_prayer",
      "midday_prayer",
      "early_evening_prayer",
      "close_of_day_prayer",
    ];
    const valid_offices =
        this.serviceType == "office" ? valid_daily_offices : valid_family_offices;
    if (!valid_offices.includes(this.$props.office)) {
      this.notFound = true;
      return;
    }
    const today_str =
        this.calendarDate.getFullYear() +
        "-" +
        (this.calendarDate.getMonth() + 1) +
        "-" +
        this.calendarDate.getDate();
    const settings = this.$store.state.settings;
    const queryString = Object.keys(settings)
        .map((key) => key + "=" + settings[key])
        .join("&");
    let data = null;
    try {
      data = await this.$http.get(
          `${process.env.VUE_APP_API_URL}api/v1/${this.serviceType}/${this.office}/` +
          today_str +
          "?" +
          queryString
      );
    } catch (e) {
      this.error =
          "There was an error retrieving the office. Please try again.";
      this.loading = false;
      return;
    }
    this.modules = data.data.modules;
    this.card = data.data.calendar_day;
    this.error = false;
    this.loading = false;
  },
  methods: {
    setFontSize(value) {
      const office = document.getElementById("office")
      if (office) {
        office.style["font-size"] = `${value}px`;
        document.querySelectorAll("office p").forEach((p) => {
          p.style["font-size"] = `${value}px`;
          p.style["line-height"] = `${value * 1.6}px`;
        });
      }
      localStorage.fontSize = this.fontSize;
    },
    displayFontSize(value) {
      return `${value}px`;
    },
  },
};
</script>
