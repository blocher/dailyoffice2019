<template>
  <PageNotFound v-if="notFound" />
  <div v-else class="litany-page">
    <header class="page litany-head">
      <!-- The text's own heading is the visible title, as in the book. -->
      <h1 class="visually-hidden">The Great Litany</h1>

      <Loading v-if="loading" />
      <UiAlert v-if="error" tone="error" :title="error" />

      <section
        v-if="!loading && !error"
        id="litany-settings"
        class="litany-options"
        aria-label="Litany options"
      >
        <UiField label="Form" for-id="litany-form" class="litany-options__form">
          <UiSelect
            id="litany-form"
            :model-value="currentForm"
            :options="formOptions"
            @update:model-value="changeForm"
          />
        </UiField>
        <UiField label="Language">
          <UiSegmented
            :model-value="currentLanguage"
            :options="languageOptions"
            aria-label="Language"
            @update:model-value="changeLanguage"
          />
        </UiField>
      </section>
    </header>

    <template v-if="!loading && !error && selected">
      <div class="book-opening">
        <Ornament glyph="o" />
      </div>
      <p class="litany-book">
        <UiButton
          variant="quiet"
          size="sm"
          icon="book"
          @click="bookOpen = true"
        >
          Book view
          <span v-if="discovery.bookViewNew" class="badge-new">New</span>
        </UiButton>
      </p>

      <div id="main" class="book litany">
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

      <BookReader
        v-model:open="bookOpen"
        title="The Great Litany"
        :subtitle="selected.name"
        :show-title="false"
      >
        <OfficeLines :modules="[{ name: 'litany', lines: selected.lines }]" />
      </BookReader>
    </template>
  </div>
</template>

<script>
// @ is an alias to /src
import Loading from '@/components/Loading.vue';
import PageNotFound from '@/views/PageNotFound.vue';
import OfficeHeading from '@/components/OfficeHeading.vue';
import OfficeCongregation from '@/components/OfficeCongregation.vue';
import OfficeLeader from '@/components/OfficeLeader.vue';
import OfficeRubric from '@/components/OfficeRubric.vue';
import OfficeSpacer from '@/components/OfficeSpacer.vue';
import BookReader from '@/components/BookReader.vue';
import { discoveryState } from '@/helpers/discovery';
import OfficeLines from '@/components/OfficeLines.vue';

const LANGUAGES = ['Contemporary', 'Traditional'];

// "The Supplication (Traditional)" -> { form: 'The Supplication', language: 'Traditional' }
function splitServiceName(name) {
  const match = /^(.*?)\s*\((Contemporary|Traditional)\)\s*$/.exec(name);
  if (!match) return { form: name, language: null };
  return { form: match[1], language: match[2] };
}

export default {
  name: 'Litany',
  components: {
    Loading,
    PageNotFound,
    OfficeHeading,
    OfficeCongregation,
    OfficeLeader,
    OfficeRubric,
    OfficeSpacer,
    BookReader,
    OfficeLines,
  },
  props: {},
  data() {
    return {
      loading: true,
      bookOpen: false,
      discovery: discoveryState,
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
    currentForm() {
      return this.service ? splitServiceName(this.service).form : '';
    },
    currentLanguage() {
      return this.service ? splitServiceName(this.service).language : null;
    },
    // Each form of the litany, in the order the API gives them.
    formOptions() {
      const forms = [];
      this.services.forEach((service) => {
        const { form } = splitServiceName(service.name);
        if (!forms.includes(form)) forms.push(form);
      });
      return forms.map((form) => ({ value: form, label: form }));
    },
    languageOptions() {
      return LANGUAGES.filter((language) =>
        this.services.some(
          (service) => splitServiceName(service.name).language === language
        )
      ).map((language) => ({ value: language, label: language }));
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
    // Find the service for a form + language, falling back to any service
    // in that form if the exact pairing does not exist.
    findService(form, language) {
      const inForm = this.services.filter(
        (service) => splitServiceName(service.name).form === form
      );
      return (
        inForm.find(
          (service) => splitServiceName(service.name).language === language
        ) || inForm[0]
      );
    },
    changeForm(form) {
      const service = this.findService(form, this.currentLanguage);
      if (service) this.changeService(service.name);
    },
    changeLanguage(language) {
      const service = this.findService(this.currentForm, language);
      if (service) this.changeService(service.name);
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
      // Update the address without discarding the router's history state.
      window.history.replaceState(window.history.state, '', link);
    },
  },
};
</script>

<style scoped>
.litany-head {
  padding-bottom: 0;
}

.litany-options {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: center;
  gap: var(--space-4);
  padding-bottom: var(--space-5);
  border-bottom: 1px solid var(--rule);
}

.litany-options__form {
  flex: 1 1 16rem;
  max-width: 26rem;
  min-width: 0;
}

.litany-options :deep(.ui-field__label) {
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
  color: var(--ink-faint);
}
.litany-book {
  margin: calc(var(--space-2) * -1) 0 var(--space-2);
  text-align: center;
}
</style>
