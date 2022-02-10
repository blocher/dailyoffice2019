<template>
  <div class="small-container home office">
    <Loading v-if="loading" />

    <CalendarCard
      :office="office"
      :calendarDate="calendarDate"
      :card="card"
      v-if="!loading"
    />
    <el-alert v-if="error" :title="error" type="error" />
    <OfficeNav :calendarDate="calendarDate" :selectedOffice="office" />

    <div class="font-size-block my-2">
      <div class="w-1/6 inline-block">
        <font-awesome-icon :icon="['fad', 'font-case']" size="sm" />
      </div>
      <div class="w-2/3 inline-block">
        <el-slider
          class="w-3/4"
          :min="sliderMin"
          :max="sliderMax"
          v-model="fontSize"
          v-on:input="setFontSize"
          :format-tooltip="displayFontSize"
        ></el-slider>
      </div>
      <div class="w-1/6 inline-block text-right">
        <font-awesome-icon :icon="['fad', 'font-case']" size="lg" />
      </div>
    </div>

    <div id="office">
      <div v-for="module in modules" v-bind:key="module.name">
        <div v-for="line in module.lines" v-bind:key="line.content">
          <OfficeHeading
            v-if="line.line_type == 'heading'"
            v-bind:line="line"
          />
          <OfficeSubheading
            v-if="line.line_type == 'subheading'"
            v-bind:line="line"
          />
          <OfficeCitation
            v-if="line.line_type == 'citation'"
            v-bind:line="line"
          />
          <OfficeHTML v-if="line.line_type == 'html'" v-bind:line="line" />
          <OfficeLeader v-if="line.line_type == 'leader'" v-bind:line="line" />
          <OfficeLeaderDialogue
            v-if="line.line_type == 'leader_dialogue'"
            v-bind:line="line"
          />
          <OfficeCongregation
            v-if="line.line_type == 'congregation'"
            v-bind:line="line"
          />
          <OfficeCongregationDialogue
            v-if="line.line_type == 'congregation_dialogue'"
            v-bind:line="line"
          />

          <OfficeRubric v-if="line.line_type == 'rubric'" v-bind:line="line" />
          <OfficeSpacer v-if="line.line_type == 'spacer'" />
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

export default {
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
    };
  },
  mounted() {
    if (localStorage.fontSize) {
      this.fontSize = parseInt(localStorage.fontSize);
    } else {
      localStorage.fontSize = this.fontSize;
    }
    this.setFontSize(this.fontSize);
  },
  async created() {
    const valid_offices = [
      "morning_prayer",
      "midday_prayer",
      "evening_prayer",
      "compline",
    ];
    if (!valid_offices.includes(this.$props.office)) {
      await this.$router.replace({ name: "not_found" });
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
        `${process.env.VUE_APP_API_URL}api/v1/office/${this.office}/` +
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
      document.getElementById("office").style["font-size"] = `${value}px`;
      localStorage.fontSize = this.fontSize;
    },
    displayFontSize(value) {
      return `${value}px`;
    },
  },
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
  },
  props: ["office", "calendarDate"],
};
</script>
