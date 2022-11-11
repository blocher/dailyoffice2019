<template>
  <div class="small-container">
    <Loading v-if="loading"/>
    <div>
      <h1>Collects</h1>
      <div class="flex justify-center">
        <el-checkbox-group v-model="selectedCollectTypes" size="large">
          <el-checkbox
v-for="collectType in collects" :key="collectType.uuid" class="m-0" border
                       :label="collectType.uuid">
            {{ collectType.name }}
          </el-checkbox>
        </el-checkbox-group>
      </div>
      <FontSizer v-if="readyToSetFontSize"/>

      <div class="flex justify-center full-width">
        <el-input
            v-model="search" class="full-width m-2" placeholder="Filter by word or phrase">
          <template #prefix>
            <el-icon class="el-input__icon">
              <font-awesome-icon :icon="['fad', 'search']"/>
            </el-icon>
          </template>
        </el-input>
      </div>
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
        <h4>{{ subcategory.name }}</h4>
        <el-collapse>
          <div v-for="collect in subcategory.collects" :key="collect.uuid">
            <Collect :key="collect.uuid" :collect=collect :traditional="traditional"/>
          </div>
        </el-collapse>
      </div>
    </div>


  </div>

</template>

<script>
import Loading from "@/components/Loading";
import CollectsFilters from "@/components/CollectsFilters";
import Collect from "@/components/Collect";
import FontSizer from "@/components/FontSizer";


export default {
  components: {Loading, CollectsFilters, Collect, FontSizer},
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

    };
  },
  computed: {
    collectCategoriesToShow() {
      return this.collects.filter((category) => {
        console.log(category, this.selectedCollectTypes);
        return this.selectedCollectTypes.includes(category.uuid);
      });
    },
  },
  watch: {
    search(val, oldVal) {
      this.filterCollects(this.categories);
    }
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
    this.error = false;
    this.loading = false;
    this.readyToSetFontSize = true;
  },
  methods: {
    setTraditional() {
      localStorage.setItem("traditionalCollects", this.traditional);
    },
    setDefaultFilter() {
      if (!this.selectedCollectTypes.length) {
        this.selectedCollectTypes = this.collects.map((category) => category.uuid);
      }
    }
  },
};
</script>

<style scoped lang="scss">
body h4 {
  text-align: left;
  margin: 2em 0;
}
</style>
