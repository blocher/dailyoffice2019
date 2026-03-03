<template>
  <div class="small-container home office">
    <Loading v-if="loading && !notFound" />
    <PageNotFound v-if="notFound" />
    <el-alert v-if="error" :title="error" type="error" />
    <header class="office-header mb-8">
      <h1 class="text-center">The Great Litany and the Supplication</h1>
      <div v-if="!loading && !notFound" id="readings" class="space-y-6">
        <div
          id="litany-settings"
          class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-100 dark:border-gray-700 shadow-sm mt-6 mb-6"
        >
          <div class="mb-2">
            <h4
              class="text-sm font-semibold uppercase tracking-wider text-gray-500 mb-2"
            >
              Service
            </h4>
            <el-select
              v-model="service"
              class="w-full"
              size="large"
              @change="changeService"
            >
              <el-option-group label="Contemporary Language">
                <el-option
                  v-for="item in contemporaryServices"
                  :key="item.name"
                  :label="item.name"
                  :value="item.name"
                />
              </el-option-group>
              <el-option-group label="Traditional Language">
                <el-option
                  v-for="item in traditionalServices"
                  :key="item.name"
                  :label="item.name"
                  :value="item.name"
                />
              </el-option-group>
            </el-select>
          </div>
        </div>
        <DisplaySettingsModule v-if="!loading && !error && !notFound" />
      </div>
    </header>
  </div>
  <div v-if="!loading && !error" id="main" class="main litany book-content">
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
import Loading from '@/components/Loading.vue';
import DisplaySettingsModule from '@/components/DisplaySettingsModule.vue';
import PageNotFound from '@/views/PageNotFound.vue';
import OfficeHeading from '@/components/OfficeHeading.vue';
import OfficeCongregation from '@/components/OfficeCongregation.vue';
import OfficeLeader from '@/components/OfficeLeader.vue';
import OfficeRubric from '@/components/OfficeRubric.vue';
import OfficeSpacer from '@/components/OfficeSpacer.vue';

export default {
  name: 'Litany',
  components: {
    Loading,
    DisplaySettingsModule,
    PageNotFound,
    OfficeHeading,
    OfficeCongregation,
    OfficeLeader,
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
    this.service = 'Great Litany';
    try {
      const data = await this.$http.get(
        `${import.meta.env.VITE_API_URL}api/v1/litany`
      );
      this.modules = data['data']['modules'];
      this.services = this.modules.map((module) => {
        return {
          name: module.name,
          active: false,
        };
      });

      this.contemporaryServices = this.services.filter((service) => {
        return service.name.includes('Contemporary');
      });
      this.traditionalServices = this.services.filter((service) => {
        return service.name.includes('Traditional');
      });
      this.contemporaryServices[0].active = true;
      this.selected = this.contemporaryServices[0];
      this.changeService(this.selected.name);
    } catch {
      this.error =
        'There was an error retrieving the litany. Please try again.';
      this.loading = false;
      return;
    }
    this.error = false;
    this.loading = false;
  },
  methods: {
    serviceLink: function () {
      return `/litany`;
    },
    changeService: function (service) {
      this.service = service;
      this.selected = this.modules.find((module) => module.name === service);
      this.contemporaryServices.forEach((service) => {
        if (service.name === this.service) {
          service.active = true;
        } else {
          service.active = false;
        }
      });
      this.traditionalServices.forEach((service) => {
        if (service.name === this.service) {
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

.el-select {
  width: 100%;
}
</style>
