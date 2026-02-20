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
      <div class="flex justify-center flex-wrap">
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

      <!--      <div class="flex justify-center full-width">-->
      <!--        <el-input-->
      <!--            v-model="search" class="full-width m-2" placeholder="Filter by word or phrase">-->
      <!--          <template #prefix>-->
      <!--            <el-icon class="el-input__icon">-->
      <!--              <font-awesome-icon :icon="['fad', 'search']"/>-->
      <!--            </el-icon>-->
      <!--          </template>-->
      <!--        </el-input>-->
      <!--      </div>-->

      <div class="flex justify-center full-width">
        <el-switch
          v-model="traditional"
          size="large"
          active-text="Traditional"
          inactive-text="Contemporary"
          class="align-center mt-4"
          @change="setTraditional"
        />
      </div>
      <el-alert v-if="error" :title="error" type="error" />
    </div>
  </div>
  <DisplaySettingsModule v-if="!loading && !error" />
  <div v-if="!loading && !error" id="main">
    <!--    <div v-if="displayedCollects.length < 1" class="h-96">-->
    <!--      <h3>No results</h3>-->
    <!--      <p class="text-center"><em>There are no collects that match your search terms and filters.</em></p>-->
    <!--    </div>-->

    <div v-for="category in collectCategoriesToShow" :key="category.uuid">
      <h3>{{ category.name }}</h3>
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
</template>

<script>
import Loading from '@/components/Loading.vue';
import DisplaySettingsModule from '@/components/DisplaySettingsModule.vue';
import CollectsSubcategory from '@/components/CollectsSubcategory.vue';
import { DynamicStorage } from '@/helpers/storage';

export default {
  components: {
    Loading,
    DisplaySettingsModule,
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
