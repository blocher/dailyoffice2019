<template>
  <div class="small-container">
    <div class="about">
      <h1>About this site</h1>
      <FontSizer v-if="readyToSetFontSize" />
      <Loading v-if="loading" />
      <el-alert v-if="error" :title="error" type="error" />
    </div>
  </div>
  <div v-if="!loading && !error" id="main">
    <div v-if="mode == 'web'">
      <div v-for="item in aboutItems" :key="item.uuid">
        <h3 v-html="item.question_for_web"></h3>
        <p v-html="item.answer_for_web"></p>
      </div>
    </div>
    <div v-if="mode == 'app'">
      <div v-for="item in aboutItems" :key="item.uuid">
        <h3 v-html="item.question_for_app"></h3>
        <p v-html="item.answer_for_app"></p>
      </div>
    </div>
  </div>
</template>

<script>
import Loading from '@/components/Loading.vue';
import FontSizer from '@/components/FontSizer.vue';
import { Capacitor } from '@capacitor/core';

export default {
  components: { Loading, FontSizer },
  data() {
    return {
      aboutItems: null,
      mode: Capacitor.getPlatform() != 'web' ? 'app' : 'web',
      error: null,
      loading: true,
      readyToSetFontSize: false,
    };
  },
  async created() {
    let data = null;
    try {
      data = await this.$http.get(
        `${import.meta.env.VITE_API_URL}api/v1/about`
      );
    } catch {
      this.error =
        'There was an error retrieving the About FAQ. Please try again.';
      this.loading = false;
      return;
    }
    this.aboutItems = data.data;
    this.error = false;
    this.loading = false;
    this.readyToSetFontSize = true;
  },
};
</script>
