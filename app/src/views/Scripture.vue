<template>
  <div class="page">
    <header class="page-header">
      <p class="eyebrow">Scripture preview</p>
      <h1 class="page-title">{{ passage }}</h1>
    </header>
    <Loading v-if="loading" />
    <UiAlert v-if="error" tone="error" :title="error" />
  </div>
  <div v-if="!loading && !error" class="book scripture">
    <section v-for="version in versions" :key="version.label">
      <h2>{{ version.label }}</h2>
      <div v-html="version.html"></div>
    </section>
  </div>
</template>

<script>
import Loading from '@/components/Loading.vue';

export default {
  components: { Loading },
  data() {
    return {
      passage: null,
      data: null,
      error: null,
      loading: true,
      esv: '-',
      kjv: '-',
      rsv: '-',
    };
  },
  computed: {
    versions() {
      return [
        { label: 'ESV', html: this.esv },
        { label: 'KJV', html: this.kjv },
        { label: 'RSV', html: this.rsv },
      ];
    },
  },
  async created() {
    this.passage = this.$route.params.passage;
    try {
      const data = await this.$http.get(
        `${import.meta.env.VITE_API_URL}api/v1/scripture/${this.passage}`
      );
      this.data = data.data;
      this.kjv = data.data.kjv;
      this.rsv = data.data.rsv;
      this.esv = data.data.esv;
    } catch {
      this.error =
        'There was an error retrieving the passage. Please try again.';
      this.loading = false;
      return;
    }
    this.error = false;
    this.loading = false;
  },
};
</script>

<style scoped>
.page {
  padding-bottom: 0;
}

.scripture section + section {
  margin-top: 1.5em;
}
</style>
