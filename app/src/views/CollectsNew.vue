<template>
  <div class="small-container">
    <Loading v-if="loading"/>
    <div>
      <h1>Collects</h1>
      <div class="flex justify-center">
        <el-checkbox-group v-model="selectedCollectTypes" size="large">
          <el-checkbox
              v-for="collectType in collects" :key="collectType.uuid" border
              :label="collectType.uuid">
            {{ collectType.name }}
          </el-checkbox>
        </el-checkbox-group>
      </div>
      <div class="flex justify-center flex-wrap">
        <el-button size="small" class="mb-1" @click="expandAll()">{{ showAllText }}</el-button>
        <el-button size="small" class="mb-1" @click="collapseAll()">
          {{ hideAllText }}
        </el-button>
        <el-button size="small" class="mb-1" @click="showOnlySelected">{{ showOnlyText }}
        </el-button>

      </div>
      <div class="flex justify-center">


      </div>
      <FontSizer v-if="readyToSetFontSize"/>

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
      <el-alert
          v-if="error" :title="error"
          type="error"
      />
    </div>
  </div>
  <div v-if="!loading && !error" id="main">

    <!--    <div v-if="displayedCollects.length < 1" class="h-96">-->
    <!--      <h3>No results</h3>-->
    <!--      <p class="text-center"><em>There are no collects that match your search terms and filters.</em></p>-->
    <!--    </div>-->

    <div v-for="category in collectCategoriesToShow" :key="category.uuid">
      <h3>{{ category.name }}</h3>
      <div v-for="subcategory in category.subcategories" :key="subcategory.uuid">
        <CollectsSubcategory
            ref="subcategories" :traditional="traditional" :subcategory="subcategory" :extra-collects="extraCollects"
            @extra-collects-changed="setExtraCollects"
        />
      </div>
    </div>

  </div>

</template>

<script>
import Loading from "@/components/Loading";
import CollectsFilters from "@/components/CollectsFilters";
import Collect from "@/components/Collect";
import FontSizer from "@/components/FontSizer";
import CollectsSubcategory from "@/components/CollectsSubcategory";

export default {
  components: {Loading, CollectsFilters, Collect, FontSizer, CollectsSubcategory},
  data() {
    return {
      collects: null,
      loading: true,
      error: false,
      traditional: false,
      search: "",
      readyToSetFontSize: false,
      selectedCollectTypes: [],
      allCollects: [],
      openedItems: [],
      defaultDict: {},
      checkList: [],
      offices: ["Morning Prayer", "Midday Prayer", "Evening Prayer", "Compline"],
      showAllText: "Show All",
      showAllDefaultText: "Show All",
      hideAllText: "Hide All",
      hideAllDefaultText: "Hide All",
      showOnlyText: "Show Only Selected Prayers",
      showOnlyDefaultText: "Show Only Selected Prayers",
      extraCollects: {},
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
    // search(val, oldVal) {
    //   this.filterCollects(this.categories);
    // },
    selectedCollectTypes() {
      this.readyToSetFontSize = false;
      this.$nextTick(() => {
        this.readyToSetFontSize = true;
      });
    },
  },
  async mounted() {
    const traditional = localStorage.getItem("traditionalCollects", false);
    if (traditional == "true" || traditional == true) {
      this.traditional = true;
    } else {
      this.traditional = false;
    }
    this.setTraditional();
    let data = null;

    try {
      data = await this.$http.get(
          `${process.env.VUE_APP_API_URL}api/v1/grouped_collects`
      );
    } catch (e) {
      this.error =
          "There was an error retrieving the collects. Please try again.";
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
    this.setDefaultFilter()
    this.setExtraCollects()
    this.error = false;
    this.loading = false;
    this.readyToSetFontSize = true;
  },
  methods: {
    setExtraCollects() {
      this.extraCollects = JSON.parse(localStorage.getItem('extraCollects')) || this.defaultDict;
      // this.offices.forEach((office) => {
      //   if (extraCollects[office].includes(this.collect.uuid)) {
      //     this.extraCollectsList.push(office)
      //   }
      // });
    },
    setTraditional() {
      localStorage.setItem("traditionalCollects", this.traditional);
    },
    setDefaultFilter() {
      if (!this.selectedCollectTypes.length) {
        this.selectedCollectTypes = this.collects.map((category) => category.uuid);
      }
    },
    expandAll() {
      this.showAllText = "...";
      setTimeout(() => {
        this.$refs.subcategories.forEach((subcategory) => {
          subcategory.expandAll();
        });
      }, 100);
      setTimeout(() => {
        this.showAllText = this.showAllDefaultText;
      }, 2000);
    },
    collapseAll() {
      this.hideAllText = "...";
      setTimeout(() => {
        this.$refs.subcategories.forEach((subcategory) => {
          subcategory.collapseAll();
        });
      }, 100);
      setTimeout(() => {
        this.hideAllText = this.hideAllDefaultText;
      }, 2000);
    },
    showOnlySelected() {
      this.showOnlyText = "...";
      setTimeout(() => {
        const defaultDict = {}
        this.offices.forEach((office) => {
          defaultDict[office] = []
        })
        let checkList = []
        const extraCollects = JSON.parse(localStorage.getItem('extraCollects')) || this.defaultDict;
        this.offices.forEach((office) => {
          checkList = checkList.concat(extraCollects[office])
        });
        this.$refs.subcategories.forEach((subcategory) => {
          subcategory.showOnlySelected(checkList);
        });
      }, 50);
      setTimeout(() => {
        this.showOnlyText = this.showOnlyDefaultText;
      }, 2000);
    }
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
