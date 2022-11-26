<template>
  <div class="home office">
    <div class="small-container">
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
        <FontSizer/>
      </div>
    </div>
    <div id="main">
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
</template>

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
import FontSizer from "@/components/FontSizer";

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
    FontSizer,
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
      notFound: false,
    };
  },
  mounted() {
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
          + "&extra_collects="
          + this.extraCollects()
      );
    } catch (e) {
      console.log(e);
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
    extraCollects() {
      if (this.serviceType != "office") {
        return ""
      }
      const full_office_name = this.office.replace("_", " ").toLowerCase().split(' ').map((s) => s.charAt(0).toUpperCase() + s.substring(1)).join(' ');
      const extraCollects = JSON.parse(localStorage.getItem('extraCollects')) || "";
      if (!extraCollects) {
        return ""
      }
      const office_extra_collects = Object.prototype.hasOwnProperty.call(extraCollects, 'full_office_name') ? extraCollects[full_office_name].join(",") : [];
      ;
      return office_extra_collects
    }
  },
};
</script>

<style scoped>
.el-alert {
  margin-top: 2em;
}
</style>
