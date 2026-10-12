<template>
  <div class="page about">
    <header class="page-header">
      <p class="eyebrow">The Daily Office</p>
      <h1 class="page-title">About this site</h1>
      <p class="page-lede">
        Questions and answers about the site, the prayers, and the people who
        make it.
      </p>
    </header>

    <Loading v-if="loading" />
    <UiAlert v-if="error" tone="error" :title="error" />

    <div v-if="!loading && !error" class="prose">
      <section v-for="item in items" :key="item.uuid" class="faq">
        <h2 class="faq__question" v-html="item.question"></h2>
        <div class="faq__answer" v-html="item.answer"></div>
      </section>
    </div>

    <div v-if="!loading && !error" class="divider">
      <Ornament glyph="v" />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import axios from 'axios';
import DOMPurify from 'dompurify';
import { Capacitor } from '@capacitor/core';
import Loading from '@/components/Loading.vue';

const mode = Capacitor.getPlatform() !== 'web' ? 'app' : 'web';
const aboutItems = ref(null);
const error = ref(null);
const loading = ref(true);

const items = computed(() =>
  (aboutItems.value || []).map((item) => ({
    uuid: item.uuid,
    question: DOMPurify.sanitize(item[`question_for_${mode}`] || ''),
    answer: DOMPurify.sanitize(item[`answer_for_${mode}`] || '', {
      ADD_ATTR: ['target'],
    }),
  }))
);

onMounted(async () => {
  try {
    const { data } = await axios.get(
      `${import.meta.env.VITE_API_URL}api/v1/about`
    );
    aboutItems.value = data;
  } catch {
    error.value =
      'There was an error retrieving the About FAQ. Please try again.';
  }
  loading.value = false;
});
</script>

<style scoped>
.prose {
  font-family: var(--font-reading);
  font-size: max(
    17px,
    calc(var(--main-font-size) * var(--reading-scale) * 0.8)
  );
  line-height: 1.6;
  color: var(--ink);
}

.faq + .faq {
  margin-top: 1.6em;
  padding-top: 1.6em;
  border-top: 1px solid var(--rule);
}

.faq__question {
  font-size: 1.12em;
  font-weight: 400;
  font-style: italic;
  line-height: 1.3;
  color: var(--ink);
  text-wrap: balance;
}

.faq__answer {
  margin-top: 0.5em;
  overflow-wrap: break-word;
}

.faq__answer :deep(p + p) {
  margin-top: 0.7em;
}

.faq__answer :deep(ul),
.faq__answer :deep(ol) {
  margin: 0.6em 0;
  padding-left: 1.3em;
  list-style: disc;
}

.faq__answer :deep(ol) {
  list-style: decimal;
}

.faq__answer :deep(strong),
.faq__answer :deep(b) {
  font-weight: 600;
}
</style>
