<template>
  <h1>{{ office }}</h1>
  <h2>
    {{ calendarDate.year }} {{ calendarDate.month }}
    {{ formattedDate }}
  </h2>

  <div class="home office">
    <Loading v-if="loading" />
    <el-alert v-if="error" :title="error" type="error" />
    <div v-for="module in modules" v-bind:key="module.name">
      <div v-for="line in module.lines" v-bind:key="line.content">
        <OfficeHeading v-if="line.line_type == 'heading'" v-bind:line="line" />
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
        <OfficeLeader
          v-if="line.line_type == 'leader_dialogue'"
          v-bind:line="line"
        />
        <OfficeCongregation
          v-if="line.line_type == 'congregation'"
          v-bind:line="line"
        />
        <OfficeCongregation
          v-if="line.line_type == 'congregation_dialogue'"
          v-bind:line="line"
        />
        <OfficeRubric v-if="line.line_type == 'rubric'" v-bind:line="line" />
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
import OfficeRubric from "@/components/OfficeRubric";
import Loading from "@/components/Loading";

export default {
  data() {
    return {
      counter: 0,
      modules: null,
      loading: true,
      error: false,
      formattedDate: "",
    };
  },
  async created() {
    const valid_offices = [
      "morning_prayer",
      "nooday_prayer",
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
    const options = {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    };
    this.formattedDate = this.calendarDate.toLocaleDateString("en-US", options);
    const settings = this.$store.state.settings;
    const queryString = Object.keys(settings)
      .map((key) => key + "=" + settings[key])
      .join("&");
    let data = null;
    try {
      data = await this.$http.get(
        `http://127.0.0.1:8000/api/v1/office/${this.office}/` +
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
    this.errors = false;
    this.loading = false;
  },
  name: "Office",
  components: {
    OfficeHeading,
    OfficeSubheading,
    OfficeCitation,
    OfficeHTML,
    OfficeCongregation,
    OfficeLeader,
    OfficeRubric,
    Loading,
  },
  props: ["office", "calendarDate"],
};
</script>
