<template>
  <div v-cloak class="page collects-page">
    <header class="page-header">
      <h1 class="page-title">Collects</h1>
      <p class="page-lede">
        Prayers for the Christian year, the offices, and many occasions. Choose
        any to add to Morning, Midday, or Evening Prayer, or Compline.
      </p>
    </header>

    <Loading v-if="loading" />
    <UiAlert v-if="error" tone="error" :title="error" />

    <template v-if="!loading && !error">
      <section class="collects-filters" aria-label="Search and filter">
        <UiInput
          id="collects-search"
          v-model="search"
          icon="search"
          clearable
          type="search"
          placeholder="Search by word or phrase"
          aria-label="Search the collects"
        />

        <div class="collects-filters__row">
          <fieldset class="collects-filters__types">
            <legend class="collects-filters__label">Show</legend>
            <div class="collects-filters__checks">
              <UiCheckbox
                v-for="collectType in collects"
                :key="collectType.uuid"
                v-model="selectedCollectTypes"
                :value="collectType.uuid"
                :label="collectType.name"
              />
            </div>
          </fieldset>

          <div class="collects-filters__language">
            <span class="collects-filters__label">Language</span>
            <UiSegmented
              :model-value="traditional"
              :options="languageOptions"
              aria-label="Language"
              @update:model-value="changeLanguage"
            />
          </div>
        </div>
      </section>

      <div class="collects-actions">
        <button
          type="button"
          class="collects-action"
          :disabled="buttonsDisabled"
          @click="expandAll"
        >
          {{ showAllText }}
        </button>
        <button
          type="button"
          class="collects-action"
          :disabled="buttonsDisabled"
          @click="collapseAll"
        >
          {{ hideAllText }}
        </button>
        <button
          type="button"
          class="collects-action"
          :disabled="buttonsDisabled"
          @click="showOnlySelected"
        >
          <UiIcon name="bookmark" />
          {{ showOnlyText }}
        </button>
      </div>

      <div class="collects-results">
        <div v-if="collectCategoriesToShow.length === 0" class="collects-empty">
          <Ornament glyph="o" />
          <p class="collects-empty__title">No results</p>
          <p>There are no collects that match your search terms and filters.</p>
        </div>

        <section
          v-for="(category, index) in collectCategoriesToShow"
          :key="category.uuid"
          class="collects-category"
        >
          <div v-if="index" class="collects-category__break">
            <Ornament glyph="o" />
          </div>
          <h2 class="section-title collects-category__title">
            {{ category.name }}
          </h2>
          <CollectsSubcategory
            v-for="subcategory in category.subcategories"
            :key="subcategory.uuid"
            ref="subcategories"
            :traditional="traditional"
            :subcategory="subcategory"
            :extra-collects="extraCollects"
            @extra-collects-changed="setExtraCollects"
          />
        </section>
      </div>
    </template>
  </div>
</template>

<script>
import Loading from '@/components/Loading.vue';
import CollectsSubcategory from '@/components/CollectsSubcategory.vue';
import { DynamicStorage } from '@/helpers/storage';

export default {
  components: {
    Loading,
    CollectsSubcategory,
  },
  data() {
    return {
      collects: null,
      loading: true,
      error: false,
      traditional: false,
      search: '',
      selectedCollectTypes: [],
      allCollects: [],
      openedItems: [],
      defaultDict: {},
      checkList: [],
      offices: [
        'Morning Prayer',
        'Midday Prayer',
        'Evening Prayer',
        'Compline',
      ],
      languageOptions: [
        { value: false, label: 'Contemporary' },
        { value: true, label: 'Traditional' },
      ],
      showAllText: 'Expand all',
      hideAllText: 'Collapse all',
      showOnlyText: 'Show my chosen prayers',
      extraCollects: {},
      buttonsDisabled: false,
    };
  },
  computed: {
    collectCategoriesToShow() {
      if (!this.collects) return [];
      const searchQuery = this.search.toLowerCase().trim();

      return this.collects
        .filter((category) => this.selectedCollectTypes.includes(category.uuid))
        .map((category) => {
          const subcategories = category.subcategories
            .map((sub) => {
              const filteredCollects = sub.collects.filter((collect) => {
                if (!searchQuery) return true;
                const matchesTitle =
                  collect.title &&
                  collect.title.toLowerCase().includes(searchQuery);
                const matchesText =
                  collect.text &&
                  collect.text.toLowerCase().includes(searchQuery);
                const matchesTraditional =
                  collect.traditional_text &&
                  collect.traditional_text.toLowerCase().includes(searchQuery);
                return matchesTitle || matchesText || matchesTraditional;
              });

              if (filteredCollects.length > 0) {
                return { ...sub, collects: filteredCollects };
              }
              return null;
            })
            .filter((sub) => sub !== null);

          if (subcategories.length > 0) {
            return { ...category, subcategories };
          }
          return null;
        })
        .filter((cat) => cat !== null);
    },
  },
  async mounted() {
    const traditional = await DynamicStorage.getItem(
      'traditionalCollects',
      false
    );
    this.traditional = traditional === 'true' || traditional === true;
    this.setTraditional();
    let data;

    try {
      data = await this.$http.get(
        `${import.meta.env.VITE_API_URL}api/v1/grouped_collects`
      );
    } catch {
      this.error =
        'There was an error retrieving the collects. Please try again.';
      this.loading = false;
      return;
    }
    this.collects = data.data;
    this.collects.forEach((category) => {
      category.subcategories.forEach((subcategory) => {
        subcategory.collects.forEach((collect) => {
          this.allCollects.push(collect);
        });
      });
    });
    this.setDefaultFilter();
    await this.setExtraCollects();
    this.error = false;
    this.loading = false;
  },
  methods: {
    async setExtraCollects() {
      this.extraCollects =
        JSON.parse(await DynamicStorage.getItem('extraCollects')) ||
        this.defaultDict;
    },
    changeLanguage(value) {
      this.traditional = value;
      this.setTraditional();
    },
    async setTraditional() {
      await DynamicStorage.setItem('traditionalCollects', this.traditional);
    },
    setDefaultFilter() {
      if (!this.selectedCollectTypes.length && this.collects) {
        this.selectedCollectTypes = this.collects.map(
          (category) => category.uuid
        );
      }
    },
    async expandAll() {
      this.buttonsDisabled = true;
      if (this.$refs.subcategories) {
        this.$refs.subcategories.forEach((subcategory) => {
          subcategory.expandAll();
        });
      }
      this.buttonsDisabled = false;
    },
    async collapseAll() {
      this.buttonsDisabled = true;
      if (this.$refs.subcategories) {
        this.$refs.subcategories.forEach((subcategory) => {
          subcategory.collapseAll();
        });
      }
      this.buttonsDisabled = false;
    },
    async showOnlySelected() {
      this.buttonsDisabled = true;
      const defaultDict = {};
      this.offices.forEach((office) => {
        defaultDict[office] = [];
      });
      let checkList = [];
      const extraCollects =
        JSON.parse(await DynamicStorage.getItem('extraCollects')) ||
        defaultDict;
      this.offices.forEach((office) => {
        checkList = checkList.concat(extraCollects[office] || []);
      });
      if (this.$refs.subcategories) {
        this.$refs.subcategories.forEach((subcategory) => {
          subcategory.showOnlySelected(checkList);
        });
      }
      this.buttonsDisabled = false;
    },
  },
};
</script>

<style scoped>
.collects-filters {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.collects-filters__row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3) var(--space-5);
}

.collects-filters__types {
  flex: 1 1 18rem;
  min-width: 0;
}

.collects-filters__label {
  display: block;
  padding: 0;
  margin-bottom: var(--space-1);
  font-size: var(--text-sm);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
  color: var(--ink-faint);
}

.collects-filters__checks {
  display: flex;
  flex-wrap: wrap;
  column-gap: var(--space-5);
}

.collects-filters__checks :deep(.ui-check) {
  align-items: center;
  min-height: 2.75rem;
}

.collects-filters__checks :deep(.ui-check input) {
  margin-top: 0;
}

.collects-filters__language {
  flex: 0 0 auto;
}

.collects-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  column-gap: var(--space-4);
  margin-top: var(--space-4);
  padding-bottom: var(--space-2);
  border-bottom: 1px solid var(--rule);
}

.collects-action {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  min-height: 2.75rem;
  font-size: var(--text-sm);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
  color: var(--accent);
}

.collects-action:not(:disabled):hover {
  text-decoration: underline;
  text-underline-offset: 0.18em;
}

.collects-action:disabled {
  opacity: 0.5;
}

.collects-category {
  margin-top: var(--space-6);
}

.collects-category__break {
  margin: 0 auto var(--space-4);
  text-align: center;
  font-size: 1.4rem;
}

.collects-category__title {
  text-align: center;
  margin-bottom: var(--space-3);
}

.collects-empty {
  padding: var(--space-7) 0;
  text-align: center;
  font-style: italic;
  color: var(--ink-soft);
}

.collects-empty .ornament {
  font-size: 1.5rem;
  margin-bottom: var(--space-3);
}

.collects-empty__title {
  font-style: normal;
  font-size: var(--text-lg);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
  color: var(--ink);
}
</style>
