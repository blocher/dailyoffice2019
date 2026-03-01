<template>
  <div class="collects-view">
    <main v-cloak class="max-w-6xl mx-auto pt-8 pb-12 px-4 lg:pb-16">
      <header class="settings-hero">
        <h1 class="settings-hero__title text-[var(--el-text-color-primary)]">
          Collects
        </h1>
        <p class="settings-hero__description">
          Browse and search the collects of the church.
        </p>
      </header>

      <Loading v-if="loading" class="mt-8" />

      <div v-if="!loading && !error">
        <div
          class="settings-search-top mb-6 bg-[var(--el-fill-color-blank)] border border-[var(--el-border-color-light)]"
        >
          <label class="settings-search-top__label"> Search & Filter </label>
          <div class="flex flex-col gap-4">
            <div class="flex flex-col md:flex-row items-center gap-4 w-full">
              <el-input
                id="collects-search"
                v-model="search"
                clearable
                class="flex-1"
                placeholder="Search by word or phrase"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>

              <div class="flex shrink-0 w-full md:w-auto justify-end">
                <el-switch
                  v-model="traditional"
                  size="large"
                  active-text="Traditional"
                  inactive-text="Contemporary"
                  @change="setTraditional"
                />
              </div>
            </div>

            <div class="flex flex-col md:flex-row items-center gap-4 w-full">
              <div class="flex-1 w-full">
                <el-checkbox-group
                  v-model="selectedCollectTypes"
                  size="default"
                  class="flex flex-wrap gap-2 m-0"
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
          </div>
        </div>

        <div
          class="settings-display-narrow mb-8 mx-auto"
          style="width: min(100%, 58rem); max-width: none"
        >
          <DisplaySettingsModule />
        </div>

        <div class="mb-6 flex flex-wrap gap-2 justify-end">
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

        <div id="main">
          <div
            v-if="collectCategoriesToShow.length === 0"
            class="py-12 text-center text-gray-500"
          >
            <h3 class="text-xl font-semibold mb-2">No results</h3>
            <p>
              <em
                >There are no collects that match your search terms and
                filters.</em
              >
            </p>
          </div>

          <div v-for="category in collectCategoriesToShow" :key="category.uuid">
            <h3
              class="text-2xl font-bold mb-4 mt-8 text-[var(--el-text-color-primary)]"
            >
              {{ category.name }}
            </h3>
            <div
              v-for="subcategory in category.subcategories"
              :key="subcategory.uuid"
            >
              <CollectsSubcategory
                ref="subcategories"
                :traditional="traditional"
                :subcategory="subcategory"
                :extra-collects="extraCollects"
                @extra-collects-changed="setExtraCollects"
              />
            </div>
          </div>
        </div>
      </div>
    </main>
    <div class="max-w-6xl mx-auto px-4">
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

.settings-hero__title {
  margin: 0;
  font-size: clamp(1.85rem, 3.4vw, 2.45rem);
  line-height: 1.18;
  color: var(--el-text-color-primary);
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

.el-checkbox-group.m-0 {
  margin: 0 !important;
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
