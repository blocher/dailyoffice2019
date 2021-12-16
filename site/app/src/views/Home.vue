<template>
  <div class="home office">
    <h1>Today</h1>

    <div v-for="module in modules" v-bind:key="module.name">
      <div v-for="line in module.lines"  v-bind:key="line.content">
        <OfficeHeading v-if="line.line_type == 'heading'" v-bind:line="line" />
        <OfficeSubheading v-if="line.line_type == 'subheading'" v-bind:line="line" />
        <OfficeCitation v-if="line.line_type == 'citation'" v-bind:line="line" />
        <OfficeHTML v-if="line.line_type == 'html'" v-bind:line="line" />
        <OfficeLeader v-if="line.line_type == 'leader'" v-bind:line="line" />
        <OfficeLeader v-if="line.line_type == 'leader_dialogue'" v-bind:line="line" />
        <OfficeCongregation v-if="line.line_type == 'congregation'" v-bind:line="line" />
        <OfficeCongregation v-if="line.line_type == 'congregation_dialogue'" v-bind:line="line" />
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

export default {
  data() {
    return {
      counter: 0,
      modules: null,
    };
  },
  async created() {
    const today = new Date();
    const dd = String(today.getDate()).padStart(2, '0');
    const mm = String(today.getMonth() + 1).padStart(2, '0'); //January is 0!
    const yyyy = today.getFullYear();
    const today_str = yyyy + '-' + mm + '-' + dd;

    const data = await this.$http.get(
      'http://127.0.0.1:8000/api/v1/office/morning_prayer/' + today_str,
    );
    this.modules = data.data.modules;
  },
  name: "Home",
  components: {
    OfficeHeading,
    OfficeSubheading,
    OfficeCitation,
    OfficeHTML,
    OfficeCongregation,
    OfficeLeader,
    OfficeRubric,
  },
  mounted() {
    setInterval(() => {
      this.counter++;
    }, 1000);
  },
};
</script>
