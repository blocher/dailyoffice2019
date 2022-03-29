<template>
  <div class="small-container">
    <div class="about">
      <h1>Occasional Collects</h1>
    </div>
    <Loading v-if="loading" />
    <el-alert v-if="error" :title="error" type="error" />
    <div v-if="!loading && !error">
      <div class="text-center">
        <el-select
          v-model="selectedCategory"
          class="w-full"
          placeholder="Select"
          size="large"
          filterable
          @change="updateDisplayedCollects"
        >
          <el-option key="all" label="All Categories" value="all" />
          <el-option
            v-for="category in categories"
            :key="category"
            :label="category"
            :value="category"
          />
        </el-select>
      </div>
      <div v-for="collect in displayedCollects" :key="collect.order">
        <h3>{{ collect.order }}. {{ collect.title }}</h3>
        <span v-html="collect.text"></span>
        <h5>{{ collect.attribution }}</h5>
      </div>
    </div>
  </div>
</template>

<script>
import Loading from "@/components/Loading";

export default {
  components: { Loading },
  data() {
    return {
      collects: null,
      displayedCollects: null,
      categories: null,
      selectedCategory: "all",
      loading: true,
      error: false,
    };
  },
  async created() {
    let data = null;
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
    this.categories = [...new Set(this.collects.map((x) => x.category_name))];
    this.error = false;
    this.loading = false;
  },
  methods: {
    updateDisplayedCollects() {
      if (this.selectedCategory === "all") {
        this.displayedCollects = this.collects;
      } else {
        this.displayedCollects = this.collects.filter(
          (x) => x.category_name === this.selectedCategory
        );
      }
    },
  },
};
</script>
