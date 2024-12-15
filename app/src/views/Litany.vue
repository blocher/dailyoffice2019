<template>
  <div class="small-container home office">
    <Loading v-if="loading && !notFound" />
    <PageNotFound v-if="notFound" />
    <el-alert v-if="error" :title="error" type="error" />
    <h1>The Great Litany and the Supplication</h1>
    <div v-if="!loading && !notFound" id="readings">
      <el-divider />

      <el-row class="mt-2 content-stretch">
        <el-col :span="24">
          <h4 class="text-left mt-4">Contemporary Language</h4>
          <div v-for="service in contemporaryServices" :key="service.name">
            <div class="grid grid-cols-12 gap-3 even:bg-grey mb-2">
              <div class="m-auto">
                <font-awesome-icon
                  v-if="service.active"
                  :icon="['fad', 'fa-octagon-check']"
                />
              </div>
              <div class="col-span-11">
                <span v-if="service.active">{{ service.name }}</span>
                <span v-if="!service.active"
                  ><a
                    :href="serviceLink(service.name)"
                    @click.prevent="changeService(service.name)"
                    >{{ service.name }}</a
                  ></span
                >
              </div>
            </div>
          </div>
          <h4 class="text-left mt-4">Traditional Langauge</h4>
          <div v-for="service in traditionalServices" :key="service.name">
            <div class="grid grid-cols-12 gap-3 even:bg-grey mb-2">
              <div class="m-auto">
                <font-awesome-icon
                  v-if="service.active"
                  :icon="['fad', 'fa-octagon-check']"
                />
              </div>
              <div class="col-span-11">
                <span v-if="service.active">{{ service.name }}</span>
                <span v-if="!service.active"
                  ><a
                    :href="serviceLink(service.name)"
                    @click.prevent="changeService(service.name)"
                    >{{ service.name }}</a
                  ></span
                >
              </div>
            </div>
          </div>
        </el-col>
      </el-row>

      <el-divider />

      <Loading v-if="loading" />
      <FontSizer />
    </div>
  </div>
  <div v-if="!loading && !error" id="main" class="main litany">
    <div v-for="(line, index) in selected.lines" :key="index">
      <OfficeHeading v-if="line.line_type == 'heading'" :line="line" />
      <OfficeLeader v-if="line.line_type == 'leader'" :line="line" />
      <OfficeCongregation
        v-if="line.line_type == 'congregation'"
        :line="line"
      />
      <OfficeRubric v-if="line.line_type == 'rubric'" :line="line" />
      <OfficeSpacer v-if="line.line_type == 'spacer'" />
    </div>
  </div>
</template>

<script>
// @ is an alias to /src
import Loading from "@/components/Loading.vue";
import CalendarCard from "@/components/CalendarCard.vue";
import OfficeNav from "@/components/OfficeNav.vue";
import Reading from "@/components/Reading.vue";
import Collects from "@/components/Collects.vue";
import CitationGroup from "@/components/CitationGroup.vue";
import FontSizer from "@/components/FontSizer.vue";
import PageNotFound from "@/views/PageNotFound.vue";
import OfficeHeading from "@/components/OfficeHeading.vue";
import OfficeSubheading from "@/components/OfficeSubheading.vue";
import OfficeCitation from "@/components/OfficeCitation.vue";
import OfficeHTML from "@/components/OfficeHTML.vue";
import OfficeCongregation from "@/components/OfficeCongregation.vue";
import OfficeLeader from "@/components/OfficeLeader.vue";
import OfficeCongregationDialogue from "@/components/OfficeCongregationDialogue.vue";
import OfficeLeaderDialogue from "@/components/OfficeLeaderDialogue.vue";
import OfficeRubric from "@/components/OfficeRubric.vue";
import OfficeSpacer from "@/components/OfficeSpacer.vue";

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
  },
  props: {},
  data() {
    return {
      loading: true,
      error: false,
      calendarDate: null,
      card: null,
      selected: null,
      services: [],
      traditionalServices: [],
      contemporaryServices: [],
      service: null,
      notFound: false,
      modules: [],
    };
  },
  computed: {
    serviceData: function () {
      return this.services.map((service) => {
        return {
          active: service.name === this.service,
          name: service.name,
        };
      });
    },
  },
  async mounted() {
    this.loading = true;
    this.service = "Great Litany";
    try {
      const data = await this.$http.get(
        `${import.meta.env.VUE_APP_API_URL}api/v1/litany`,
      );
      this.modules = data["data"]["modules"];
      this.services = this.modules.map((module) => {
        return {
          name: module.name,
          active: false,
        };
      });

      this.contemporaryServices = this.services.filter((service) => {
        return service.name.includes("Contemporary");
      });
      this.traditionalServices = this.services.filter((service) => {
        return service.name.includes("Traditional");
      });
      this.contemporaryServices[0].active = true;
      this.selected = this.contemporaryServices[0];
      this.changeService(this.selected.name);
    } catch (e) {
      this.error =
        "There was an error retrieving the litany. Please try again.";
      this.loading = false;
      return;
    }
    this.error = false;
    this.loading = false;
  },
  methods: {
    serviceLink: function (service) {
      return `/litany`;
    },
    changeService: function (service) {
      this.service = service;
      this.selected = this.modules.find((module) => module.name === service);
      this.contemporaryServices.forEach((service) => {
        if (service.name == this.service) {
          service.active = true;
        } else {
          service.active = false;
        }
      });
      this.traditionalServices.forEach((service) => {
        if (service.name == this.service) {
          service.active = true;
        } else {
          service.active = false;
        }
      });
      const link = this.serviceLink(service);
      history.pushState({}, null, link);
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
