<template>
  <div class="small-container">
    <Loading v-if="loading"/>
    <div>
      <h1>Collects</h1>
      <div class="flex justify-center">
        <el-checkbox-group v-model="selectedCollectTypes" size="large" @change="filterType">
          <el-checkbox-button v-for="collectType in collectTypes" :key="collectType.uuid" :label="collectType.name">
            {{ collectType.name }}
          </el-checkbox-button>
        </el-checkbox-group>
      </div>
      <FontSizer v-if="readyToSetFontSize"/>
      <CollectsFilters
          v-if="!loading && !error" :filters="collectCategories"
          @update:activeFilters="filterCollects"/>
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

    <div v-if="displayedCollects.length < 1" class="h-96">
      <h3>No results</h3>
      <p class="text-center"><em>There are no collects that match your search terms and filters.</em></p>
    </div>

    <div v-for="(collects, collectType) in collectsByCollectType" :key="collectType.uuid">
      <h3>{{ collectType }}</h3>
      <div v-for="collect in collects" :key="collect.uuid">

        <p><span v-if="collect.number"><small>{{ collect.number }}&nbsp;</small></span>{{ collect.title }}</p>
      </div>
    </div>

    <Collect v-for="collect in displayedCollects" :key="collect.uuid" :collect=collect :traditional="traditional"/>
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
      displayedCollects: [],
      categories: null,
      selectedCategory: "All Categories",
      loading: true,
      error: false,
      collectCategories: [],
      traditional: false,
      search: "",
      readyToSetFontSize: false,
      collectTypes: [],
      collectsByCollectType: {},
      selectedCollectTypes: [],
    };
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

    // this.collectCategories = this.formatCollectCategories(data.data);
    try {
      data = await this.$http.get(
          `${process.env.VUE_APP_API_URL}api/v1/collects`
      );
    } catch (e) {
      this.error =
          "There was an error retrieving the collects. Please try again.";
      this.loading = false;
      return;
    }
    this.collects = data.data;

    try {
      data = await this.$http.get(
          `${process.env.VUE_APP_API_URL}api/v1/collect_categories`
      );
    } catch (e) {
      this.error =
          "There was an error retrieving the collect categories. Please try again.";
      this.loading = false;
      return;
    }
    this.setCollectTypes(data.data);


    this.displayedCollects = this.collects;
    // this.filterCollects([])
    this.error = false;
    this.loading = false;
    this.readyToSetFontSize = true;

  },
  methods: {
    filterType() {
      this.displayedCollects = this.collects.filter(collect => {
        return this.selectedCollectTypes.includes(collect.collect_type.name);
      });
    },
    setTraditional() {
      localStorage.setItem("traditionalCollects", this.traditional);
    },
    setCollectTypes(categories) {
      const category = categories.filter((category) => {
        return category.key == "source"
      })[0]

      this.collectTypes = category.tags.map((tag) => {
        return {
          id: tag.uuid,
          name: tag.name,
        }
      });

      this.collectTypes.forEach((collectType) => {
        this.collectsByCollectType[collectType.name] = this.collects.filter((collect) => {
          const tag_ids = collect.tags.map((tag) => {
            return tag.uuid;
          });
          return tag_ids.includes(collectType.id);
        });
      });

      console.log(this.collectsByCollectType)

    },
    formatCollectCategories(categories) {
      return categories.map((category) => {
        return {
          id: category.uuid,
          name: category.name,
          options: category.tags.map((tag) => {
            return {
              value: tag.uuid,
              label: tag.name,
            };
          }),
        };
      });
    },
    filterCollects(categories) {
      this.categories = categories;
      if (!categories || Object.values(categories).length === 0) {
        this.displayedCollects = this.collects;
      } else {
        let collects = this.collects;
        for (let i in Object.values(this.collectCategories)) {
          const collectCategoryType = this.collectCategories[i];
          const options = collectCategoryType.options.map((option) => {
            return option.value;
          });
          // all values in both categories and options
          const intersection = options.filter((value) => categories.includes(value));
          if (intersection.length > 0) {
            collects = collects.filter(
                (collect) => {
                  const tags = collect.tags.map((tag) => tag.uuid);
                  return intersection.some((category) => tags.includes(category));
                });
          }
        }
        this.displayedCollects = collects;
      }
      if (this.search.length > 0) {
        this.displayedCollects = this.displayedCollects.filter(collect => {
          return collect.title_and_tags.toLowerCase().includes(this.search.toLowerCase()) || collect.text.toLowerCase().includes(this.search.toLowerCase()) || collect.traditional_text.toLowerCase().includes(this.search.toLowerCase())
        });
      }
    },

  },
};
</script>
