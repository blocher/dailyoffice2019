<template>

  <div class="small-container">
    <div class="about">
      <Loading v-if="loading"/>
      <div>
        <h1>Collects</h1>
        <CollectsFilters
            v-if="!loading && !error" :filters="collectCategories"
            @update:activeFilters="filterCollects"/>
      </div>
      <el-alert
          v-if="error" :title="error"
          type="error"
      />
      <div v-if="!loading && !error">

        <div v-if="displayedCollects.length < 1">
          <p><em>There are no collects that match your filters.</em></p>
        </div>

        <div
            v-for="collect in displayedCollects" :key="collect.order"
        >
          <h3><span v-if="collect.number">{{ collect.number }}. </span>{{ collect.title }}</h3>
          <div class="text-center py-2">
            <el-tag v-for="tag in collect.tags" :key="tag.uuid" class="ml-2" type="info">{{ tag.name }}</el-tag>
          </div>
          <span v-html="collect.traditional_text"/>
          <br>
          <span v-html="collect.text"/>
          <h5>{{ collect.attribution }}</h5>


        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Loading from "@/components/Loading";
import CollectsFilters from "@/components/CollectsFilters";

export default {
  components: {Loading, CollectsFilters},
  data() {
    return {
      collects: null,
      displayedCollects: [],
      categories: null,
      selectedCategory: "All Categories",
      loading: true,
      error: false,
      collectCategories: [],
    };
  },
  async created() {
    let data = null;
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
    this.collectCategories = this.formatCollectCategories(data.data);
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

    this.displayedCollects = this.collects;
    this.error = false;
    this.loading = false;
  },
  methods: {
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
                  if (intersection.length > 0) {
                    console.log(tags, intersection, tags.some((category) => intersection.includes(category)));
                  }

                  return intersection.some((category) => tags.includes(category));
                });
          }
        }
        this.displayedCollects = collects;
      }
    }
  },
};
</script>
