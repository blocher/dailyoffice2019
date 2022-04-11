<template>
  <div class="small-container">
    <div class="about">
      <h1>About this site!</h1>
      <Loading v-if="loading"/>
      <el-alert
          v-if="error" :title="error"
          type="error"
      />
      <div v-if="!loading && !error">
        <div v-for="item in aboutItems" :key="item.uuid" :v-if="mode=='web'">
          <h3 v-html="item.question_for_web"></h3>
          <p v-html="item.answer_for_web"></p>
        </div>
        <div v-for="item in aboutItems" :key="item.uuid" :v-if="mode=='app'">
          <h3 v-html="item.question_for_app"></h3>
          <p v-html="item.answer_for_app"></p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>

import Loading from "@/components/Loading";

export default {
  components: {Loading},
  data() {
    return {
      aboutItems: null,
      mode: "web",
      error: null,
      loading: true,
    };
  },
  async created() {
    let data = null;
    try {
      data = await this.$http.get(
          `${process.env.VUE_APP_API_URL}api/v1/about`
      );
    } catch (e) {
      this.error =
          "There was an error retrieving the About FAQ. Please try again.";
      this.loading = false;
      return;
    }
    this.aboutItems = data.data;
    this.error = false;
    this.loading = false;
  }
}
</script>
