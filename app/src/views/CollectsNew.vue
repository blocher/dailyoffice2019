<template>
  <div class="collects-view">
    <main v-cloak class="px-4 pt-8 pb-12 mx-auto lg:pb-16 w-full">
      <header class="text-center settings-hero max-w-6xl mx-auto">
        <h1>Collects</h1>
      </header>

      <Loading v-if="loading" class="mt-8" />

      <div v-if="!loading && !error">
        <div
          class="settings-search-top mb-6 bg-(--el-fill-color-blank) border border-(--el-border-color-light) max-w-6xl mx-auto"
        >
          <label class="settings-search-top__label"> Search & Filter </label>
          <div class="settings-controls">
            <div class="settings-controls__primary">
              <div class="settings-controls__search">
                <el-input
                  id="collects-search"
                  v-model="internalSearch"
                  @input="handleSearchChange"
                  clearable
                  class="w-full"
                  placeholder="Search by word or phrase"
                >
                  <template #prefix>
                    <el-icon><Search /></el-icon>
                  </template>
                </el-input>
              </div>
              <div class="settings-controls__types">
                <el-checkbox-group
                  v-model="internalSelectedCollectTypes"
                  size="default"
                  class="collect-type-selector m-0"
                  @change="handleTypeSelectionChange"
                >
                  <el-checkbox
                    v-for="collectType in collects"
                    :key="collectType.uuid"
                    border
                    :label="collectType.uuid"
                    class="mr-0"
                  >
                    {{ collectType.name }}
                  </el-checkbox>
                </el-checkbox-group>
              </div>
            </div>

            <div class="collect-language-filter">
              <div class="collect-language-filter__card">
                <label class="collect-control-label">Display Versions</label>
                <el-checkbox-group
                  v-model="internalSelectedLanguages"
                  class="collect-language-selector m-0"
                  @change="handleLanguageSelectionChange"
                >
                  <el-checkbox
                    v-for="option in languageOptions"
                    :key="option.value"
                    border
                    :label="option.value"
                    class="mr-0"
                  >
                    {{ option.label }}
                  </el-checkbox>
                </el-checkbox-group>
                <p class="collect-control-hint">
                  Choose one or more versions. Multiple selections appear side
                  by side.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div
          class="mx-auto mb-8 settings-display-narrow max-w-6xl"
          style="width: min(100%, 58rem); max-width: none"
        >
          <DisplaySettingsModule />
        </div>

        <div class="flex flex-wrap gap-2 justify-end mb-6 max-w-6xl mx-auto">
          <el-button
            size="small"
            :disabled="buttonsDisabled"
            @click="expandAll"
          >
            {{ showAllText }}
          </el-button>
          <el-button
            size="small"
            :disabled="buttonsDisabled"
            @click="collapseAll"
          >
            {{ hideAllText }}
          </el-button>
          <el-button
            size="small"
            :disabled="buttonsDisabled"
            @click="showOnlySelected"
          >
            {{ showOnlyText }}
          </el-button>
        </div>

        <div
          id="main"
          class="mx-auto transition-all duration-300 relative"
          :class="[
            hasMultipleLanguagesSelected
              ? 'max-w-480! px-2! lg:px-8!'
              : 'max-w-3xl!',
            { 'opacity-50 pointer-events-none': isFiltering },
          ]"
        >
          <div
            v-if="isFiltering"
            class="absolute inset-0 z-10 flex justify-center pt-24"
          >
            <Loading />
          </div>

          <div
            v-if="collectCategoriesToShow.length === 0"
            class="py-12 text-center text-gray-500"
          >
            <h3 class="mb-2 text-xl font-semibold">No results</h3>
            <p>
              <em
                >There are no collects that match your search terms and
                filters.</em
              >
            </p>
          </div>

          <div v-for="category in collectCategoriesToShow" :key="category.uuid">
            <h3
              class="text-2xl font-bold mb-4 mt-8 text-(--el-text-color-primary)"
            >
              {{ category.name }}
            </h3>
            <div
              v-for="subcategory in category.subcategories"
              :key="subcategory.uuid"
            >
              <CollectsSubcategory
                ref="subcategories"
                :subcategory="subcategory"
                :extra-collects="extraCollects"
                :selected-languages="selectedLanguages"
                @extra-collects-changed="setExtraCollects"
              />
            </div>
          </div>
        </div>
      </div>
    </main>
    <div class="px-4 mx-auto max-w-6xl">
      <el-alert v-if="error" :title="error" type="error" />
    </div>
  </div>
</template>

<script>
import Loading from '@/components/Loading.vue';
import DisplaySettingsModule from '@/components/DisplaySettingsModule.vue';
import CollectsSubcategory from '@/components/CollectsSubcategory.vue';
import { Search } from '@element-plus/icons-vue';
import { DynamicStorage } from '@/helpers/storage';

const COLLECT_LANGUAGE_STORAGE_KEY = 'collectsNewSelectedLanguages';
const COLLECT_TYPE_STORAGE_KEY = 'collectsNewSelectedTypes';
const LANGUAGE_OPTIONS = [
  { value: 'contemporary', label: 'Contemporary' },
  { value: 'traditional', label: 'Traditional' },
  { value: 'spanish', label: 'Spanish' },
];

export default {
  components: {
    Loading,
    DisplaySettingsModule,
    CollectsSubcategory,
    Search,
  },
  data() {
    return {
      collects: null,
      loading: true,
      isFiltering: false,
      error: false,
      search: '',
      internalSearch: '',
      searchTimeout: null,
      selectedCollectTypes: [],
      internalSelectedCollectTypes: [],
      selectedLanguages: ['contemporary'],
      internalSelectedLanguages: ['contemporary'],
      lastSelectedLanguages: ['contemporary'],
      languageOptions: LANGUAGE_OPTIONS,
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
      showAllText: 'Expand All',
      showAllDefaultText: 'Expand All',
      hideAllText: 'Collapse All',
      hideAllDefaultText: 'Collapse All',
      showOnlyText: 'Expand Only Chosen Prayers',
      showOnlyDefaultText: 'Expand Only Chosen Prayers',
      extraCollects: {},
      buttonsDisabled: false,
    };
  },
  computed: {
    hasMultipleLanguagesSelected() {
      return this.selectedLanguages.length > 1;
    },
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
                const matchesSpanishTitle =
                  collect.spanish_title &&
                  collect.spanish_title.toLowerCase().includes(searchQuery);
                const matchesText =
                  collect.text &&
                  collect.text.toLowerCase().includes(searchQuery);
                const matchesTraditional =
                  collect.traditional_text &&
                  collect.traditional_text.toLowerCase().includes(searchQuery);
                const matchesSpanish =
                  collect.spanish_text &&
                  collect.spanish_text.toLowerCase().includes(searchQuery);
                return (
                  matchesTitle ||
                  matchesSpanishTitle ||
                  matchesText ||
                  matchesTraditional ||
                  matchesSpanish
                );
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
    const storedLanguages = await DynamicStorage.getItem(
      COLLECT_LANGUAGE_STORAGE_KEY
    );
    const traditional = await DynamicStorage.getItem('traditionalCollects');
    this.selectedLanguages = this.normalizeSelectedLanguages(
      storedLanguages,
      traditional
    );
    this.internalSelectedLanguages = [...this.selectedLanguages];
    this.lastSelectedLanguages = [...this.selectedLanguages];
    let data = null;

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
    await this.restoreSelectedCollectTypes();
    await this.setExtraCollects();
    await this.persistSelectedLanguages();
    this.error = false;
    this.loading = false;
  },
  methods: {
    handleSearchChange(val) {
      this.isFiltering = true;
      window.clearTimeout(this.searchTimeout);
      this.searchTimeout = window.setTimeout(() => {
        this.search = val;
        this.$nextTick(() => {
          this.isFiltering = false;
        });
      }, 300);
    },
    handleTypeSelectionChange(value) {
      this.isFiltering = true;
      window.setTimeout(async () => {
        this.selectedCollectTypes = value;
        await this.persistSelectedCollectTypes();
        this.$nextTick(() => {
          this.isFiltering = false;
        });
      }, 10);
    },
    normalizeSelectedLanguages(storedLanguages, traditionalFallback) {
      let parsedLanguages = [];

      try {
        parsedLanguages = JSON.parse(storedLanguages) || [];
      } catch {
        parsedLanguages = [];
      }

      const normalized = parsedLanguages.filter((language) =>
        this.languageOptions.some((option) => option.value === language)
      );

      if (normalized.length) {
        return [...new Set(normalized)];
      }

      return [
        traditionalFallback === 'true' || traditionalFallback === true
          ? 'traditional'
          : 'contemporary',
      ];
    },
    async persistSelectedLanguages() {
      await DynamicStorage.setItem(
        COLLECT_LANGUAGE_STORAGE_KEY,
        JSON.stringify(this.selectedLanguages)
      );

      if (
        this.selectedLanguages.length === 1 &&
        this.selectedLanguages[0] !== 'spanish'
      ) {
        await DynamicStorage.setItem(
          'traditionalCollects',
          this.selectedLanguages[0] === 'traditional'
        );
      }
    },
    async handleLanguageSelectionChange(value) {
      if (!value.length) {
        this.internalSelectedLanguages = [...this.lastSelectedLanguages];
        return;
      }

      this.isFiltering = true;
      window.setTimeout(async () => {
        this.selectedLanguages = value;
        this.lastSelectedLanguages = [...value];
        await this.persistSelectedLanguages();
        this.$nextTick(() => {
          this.isFiltering = false;
        });
      }, 10);
    },
    async setExtraCollects() {
      this.extraCollects =
        JSON.parse(await DynamicStorage.getItem('extraCollects')) ||
        this.defaultDict;
    },
    async restoreSelectedCollectTypes() {
      if (!this.collects) {
        return;
      }

      const storedTypes = await DynamicStorage.getItem(
        COLLECT_TYPE_STORAGE_KEY
      );
      let parsedTypes = [];

      try {
        parsedTypes = JSON.parse(storedTypes) || [];
      } catch {
        parsedTypes = [];
      }

      const availableTypes = new Set(
        this.collects.map((category) => category.uuid)
      );
      const restoredTypes = parsedTypes.filter((uuid) =>
        availableTypes.has(uuid)
      );

      this.selectedCollectTypes = restoredTypes.length
        ? restoredTypes
        : this.collects.map((category) => category.uuid);

      this.internalSelectedCollectTypes = [...this.selectedCollectTypes];

      await this.persistSelectedCollectTypes();
    },
    async persistSelectedCollectTypes() {
      if (!this.collects) {
        return;
      }

      await DynamicStorage.setItem(
        COLLECT_TYPE_STORAGE_KEY,
        JSON.stringify(this.selectedCollectTypes)
      );
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
        checkList = checkList.concat(extraCollects[office]);
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
[v-cloak] {
  display: none;
}

.settings-hero {
  margin-bottom: 1rem;
}

.settings-hero__description {
  margin: 0.55rem 0 0;
  max-width: 62ch;
  color: var(--el-text-color-secondary);
  font-size: 0.97rem;
}

.settings-display-narrow {
  width: min(100%, 58rem);
}

.settings-search-top {
  border: 1px solid var(--el-border-color-light);
  border-radius: 0.55rem;
  background-color: var(--el-fill-color-blank);
  padding: 0.58rem 0.66rem 0.66rem;
  margin-bottom: 0.7rem;
}

.settings-search-top__label {
  display: block;
  margin-bottom: 0.26rem;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--el-text-color-secondary);
}

.settings-controls {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(24rem, 28rem);
  gap: 1rem 1.25rem;
  align-items: start;
}

.settings-controls__primary {
  display: grid;
  gap: 1rem;
  min-width: 0;
}

.settings-controls__search,
.settings-controls__types {
  min-width: 0;
}

.collect-language-filter {
  min-width: 0;
}

.collect-language-filter__card {
  height: 100%;
  padding: 0.75rem 0.85rem;
  border: 1px solid var(--el-border-color-light);
  border-radius: 0.6rem;
  background: var(--el-fill-color-light);
}

.collect-control-label {
  display: block;
  margin-bottom: 0.55rem;
  color: var(--el-text-color-regular);
  font-size: 0.88rem;
  font-weight: 600;
}

.collect-control-hint {
  margin: 0.55rem 0 0;
  color: var(--el-text-color-secondary);
  font-size: 0.82rem;
  line-height: 1.4;
}

.collect-type-selector {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  align-items: flex-start;
}

.collect-type-selector :deep(.el-checkbox) {
  margin-right: 0;
}

.collect-language-selector {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: flex-start;
}

.collect-language-selector :deep(.el-checkbox) {
  margin-right: 0;
}

.el-checkbox-group.m-0 {
  margin: 0 !important;
}

@media (max-width: 1080px) {
  .settings-controls {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .settings-hero__description {
    font-size: 0.92rem;
  }
  .settings-display-narrow {
    width: 100%;
  }
}
</style>
