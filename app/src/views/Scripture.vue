<template>
  <div class="small-container">
    <div class="about">
      <h1>Scripture preview</h1>
      <Loading v-if="loading"/>
      <el-alert
          v-if="error" :title="error"
          type="error"
      />
      <div v-if="!loading && !error">
        {{ passage }}
        <h3>ESV</h3>
        <div v-html="esv"></div>
        <h3>KJV</h3>
        <div v-html="kjv"></div>
        <h3>RSV</h3>
        <div v-html="rsv"></div>
      </div>
    </div>
  </div>
</template>

<script>

import Loading from "@/components/Loading";
import {getURL} from "@/utils/request";

export default {
  components: {Loading},
  data() {
    return {
      passage: null,
      data: null,
      error: null,
      loading: true,
      esv: "-",
      kjv: "-",
      rsv: "-",
    };
  },
  async created() {
    let data = null;
    this.passage = this.$route.params.passage
    try {
      const data = await getURL(
          `${process.env.VUE_APP_API_URL}api/v1/scripture/${this.passage}`
      );
      this.data = data
      this.kjv = data.kjv
      this.rsv = data.rsv
      this.esv = data.esv

    } catch (e) {
      this.error =
          "There was an error retrieving the passage. Please try again.";
      this.loading = false;
      return;
    }
    this.error = false;
    this.loading = false;
  }
}
</script>
