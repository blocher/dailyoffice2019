<template>
  <div class="small-container">
    <Loading v-if="loading" />
    <div>
      <h1>Collects</h1>
      <div class="flex justify-center">
        <el-checkbox-group v-model="selectedCollectTypes" size="large">
          <el-checkbox
            v-for="collectType in collects"
            :key="collectType.uuid"
            border
            :label="collectType.uuid"
          >
            {{ collectType.name }}
          </el-checkbox>
        </el-checkbox-group>
      </div>
      <div class="flex flex-wrap justify-center">
        <el-button
          size="small"
          class="mb-1"
          :disabled="buttonsDisabled"
          @click="expandAll()"
          >{{ showAllText }}
        </el-button>
        <el-button
          size="small"
          class="mb-1"
          :disabled="buttonsDisabled"
          @click="collapseAll()"
        >
          {{ hideAllText }}
        </el-button>
        <el-button
          size="small"
          class="mb-1"
          :disabled="buttonsDisabled"
          @click="showOnlySelected"
          >{{ showOnlyText }}
        </el-button>
      </div>
      <div class="flex justify-center"></div>
      <FontSizer v-if="readyToSetFontSize" />

      <div class="flex justify-center mt-4 full-width">
        <el-checkbox-group v-model="selectedVersions" @change="setVersions">
          <el-checkbox-button
            v-for="version in versionOptions"
            :key="version.value"
            :label="version.value"
          >
            {{ version.label }}
          </el-checkbox-button>
        </el-checkbox-group>
      </div>
      <el-alert v-if="error" :title="error" type="error" />
    </div>
  </div>
  <div v-if="!loading && !error" id="main">
    <div v-for="category in collectCategoriesToShow" :key="category.uuid">
      <h3>{{ category.name }}</h3>
      <div
        v-for="subcategory in category.subcategories"
        :key="subcategory.uuid"
      >
        <CollectsSubcategory
          ref="subcategories"
          :selected-versions="selectedVersions"
          :subcategory="subcategory"
          :extra-collects="extraCollects"
          @extra-collects-changed="setExtraCollects"
        />
      </div>
    </div>
  </div>
</template>

<script>
import Loading from '@/components/Loading.vue';
import FontSizer from '@/components/FontSizer.vue';
import CollectsSubcategory from '@/components/CollectsSubcategory.vue';
import { DynamicStorage } from '@/helpers/storage';

export default {
  components: {
    Loading,
    FontSizer,
    CollectsSubcategory,
  },
  data() {
    return {
      collects: null,
      loading: true,
      error: false,
      selectedVersions: ['contemporary'],
      versionOptions: [
        { label: 'Contemporary', value: 'contemporary' },
        { label: 'Traditional', value: 'traditional' },
        { label: 'Spanish', value: 'spanish' },
      ],
      search: '',
      readyToSetFontSize: false,
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
      return this.collects.filter((category) => {
        return this.selectedCollectTypes.includes(category.uuid);
      });
    },
  },
  watch: {
    selectedVersions() {
      this.readyToSetFontSize = false;
      this.$nextTick(() => {
        this.readyToSetFontSize = true;
      });
    },
    selectedCollectTypes() {
      this.readyToSetFontSize = false;
      this.$nextTick(() => {
        this.readyToSetFontSize = true;
      });
    },
  },
  async mounted() {
    const storedVersions = await DynamicStorage.getItem('collectVersions');
    if (storedVersions) {
      try {
        this.selectedVersions = JSON.parse(storedVersions);
      } catch {
        this.selectedVersions = ['contemporary'];
      }
    } else {
      // Migrate legacy setting
      const traditional = await DynamicStorage.getItem(
        'traditionalCollects',
        false
      );
      if (traditional === 'true' || traditional === true) {
        this.selectedVersions = ['traditional'];
      } else {
        this.selectedVersions = ['contemporary'];
      }
    }

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
    this.readyToSetFontSize = true;
  },
  methods: {
    async setExtraCollects() {
      this.extraCollects =
        JSON.parse(await DynamicStorage.getItem('extraCollects')) ||
        this.defaultDict;
    },
    async setVersions() {
      await DynamicStorage.setItem(
        'collectVersions',
        JSON.stringify(this.selectedVersions)
      );
    },
    setDefaultFilter() {
      if (!this.selectedCollectTypes.length) {
        this.selectedCollectTypes = this.collects.map(
          (category) => category.uuid
        );
      }
    },
    async expandAll() {
      this.buttonsDisabled = true;
      await this.$nextTick();
      await this.$refs.subcategories.forEach((subcategory) => {
        subcategory.expandAll();
      });
      await this.$nextTick();
      this.buttonsDisabled = false;
    },
    async collapseAll() {
      this.buttonsDisabled = true;
      await this.$nextTick();
      await this.$refs.subcategories.forEach((subcategory) => {
        subcategory.collapseAll();
      });
      await this.$nextTick();
      this.buttonsDisabled = false;
    },
    async showOnlySelected() {
      this.buttonsDisabled = true;
      await this.$nextTick();
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
      this.$refs.subcategories.forEach((subcategory) => {
        subcategory.showOnlySelected(checkList);
      });
      this.buttonsDisabled = false;
    },
  },
};
</script>

<style scoped lang="scss">
body h4 {
  text-align: left;
  margin: 2em 0;
}

.upside-down span {
  transform: scale(-1, 1);
}

.el-checkbox-group {
  margin: 20px 0;
}

.el-checkbox {
  @media (max-width: 675px) {
    width: 100%;
    margin-bottom: 10px;
  }
}

.el-collapse-item__header {
  height: auto !important;
  margin: 2px 0;
}
</style>
