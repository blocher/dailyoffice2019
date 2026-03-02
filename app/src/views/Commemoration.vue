<template>
  <div class="commemoration-view">
    <main v-cloak class="max-w-5xl mx-auto pt-8 pb-12 px-4 lg:pb-16">
      <div v-if="!loading && commemoration">
        <header class="text-center mb-8">
          <h1
            class="text-3xl md:text-4xl font-bold text-[var(--el-text-color-primary)] m-0 mb-2 p-0"
          >
            {{ commemoration.name }}
          </h1>
          <h3
            v-if="commemoration.date_string"
            class="text-lg md:text-xl text-[var(--el-text-color-secondary)] m-0 p-0 font-normal"
          >
            {{ commemoration.date_string }}
          </h3>
        </header>
      </div>

      <div class="mb-6 max-w-2xl mx-auto">
        <el-alert type="warning" show-icon :closable="false">
          <template #title>
            <p class="leading-relaxed m-0">
              This is an <strong>experimental</strong> feature. The information
              is compiled from <strong>unofficial</strong> sources, and was
              built with assistance by AI. While we attempt to cite and link to
              all original sources, there may still be errors. Please report any
              factual or theological errors to
              <a
                href="mailto:feedback@dailyoffice2019.com"
                class="text-[var(--accent-color)] hover:underline"
                >feedback@dailyoffice2019.com</a
              >
              for correction.
            </p>
          </template>
        </el-alert>
      </div>

      <div
        class="flex justify-between items-center mb-6 text-sm md:text-base font-semibold max-w-4xl mx-auto px-2 gap-4"
      >
        <div class="text-left flex-1 min-w-0">
          <a
            v-if="!loading && commemoration?.previous_commemoration"
            :href="commemoration.previous_commemoration.uuid"
            :title="commemoration.previous_commemoration.name"
            class="flex items-center gap-2 hover:text-[var(--accent-color)] transition-colors no-underline w-full"
          >
            <font-awesome-icon :icon="['fad', 'left']" class="shrink-0" />
            <span class="truncate">{{
              commemoration.previous_commemoration.name
            }}</span>
          </a>
        </div>
        <div class="text-right flex-1 min-w-0">
          <a
            v-if="!loading && commemoration?.next_commemoration"
            :href="commemoration.next_commemoration.uuid"
            :title="commemoration.next_commemoration.name"
            class="flex items-center justify-end gap-2 hover:text-[var(--accent-color)] transition-colors no-underline w-full"
          >
            <span class="truncate">{{
              commemoration.next_commemoration.name
            }}</span>
            <font-awesome-icon :icon="['fad', 'right']" class="shrink-0" />
          </a>
        </div>
      </div>

      <el-card
        v-if="!loading && commemoration"
        class="shadow-sm border border-[var(--el-border-color-light)] max-w-4xl mx-auto"
      >
        <template #header>
          <div
            class="flex flex-col sm:flex-row items-center sm:items-start gap-6"
          >
            <div
              v-if="validImages.ai_image_1"
              class="shrink-0 w-full sm:w-[200px] flex justify-center"
            >
              <img
                :src="commemoration.ai_image_1"
                :alt="commemoration.name"
                class="w-full max-w-[250px] sm:max-w-full h-auto rounded-lg object-contain shadow-sm"
              />
            </div>
            <div
              class="text-lg leading-relaxed italic text-[var(--el-text-color-regular)] self-center text-center sm:text-left"
            >
              <p class="m-0">{{ commemoration.ai_one_sentence }}</p>
            </div>
          </div>
        </template>

        <div v-if="validImages.image_link" class="mb-8 flex justify-center">
          <img
            :src="commemoration.image_link"
            class="max-w-full h-auto max-h-[400px] rounded-lg shadow-sm object-contain"
          />
        </div>

        <div class="space-y-8 flex flex-col gap-8">
          <el-alert
            type="success"
            :closable="false"
            class="border border-green-200 dark:border-green-900 bg-green-50 dark:bg-green-900/20"
          >
            <template #title>
              <div class="text-base text-green-900 dark:text-green-100 p-2">
                <p class="mb-2 leading-relaxed">
                  <strong
                    v-html="
                      addCitations(
                        commemoration.ai_quote,
                        commemoration.ai_quote_citations
                      )
                    "
                  ></strong>
                </p>
                <p
                  v-if="commemoration.ai_quote_by"
                  class="opacity-90 m-0 text-sm"
                >
                  <em>— {{ commemoration.ai_quote_by }}</em>
                </p>
              </div>
            </template>
          </el-alert>

          <div class="flex flex-col lg:flex-row gap-8 mt-8">
            <div class="lg:w-1/3 shrink-0">
              <el-card
                class="bg-[var(--el-fill-color-light)] border-none shadow-none h-full"
                body-style="padding: 1.5rem;"
              >
                <h4
                  class="text-sm font-bold uppercase tracking-wider mb-4 text-[var(--el-text-color-secondary)] m-0 p-0 text-left"
                >
                  Key Facts
                </h4>
                <ul
                  class="space-y-3 list-disc pl-5 text-[var(--el-text-color-regular)] m-0"
                >
                  <li
                    v-for="(point, index) in commemoration.ai_bullet_points"
                    :key="index"
                    class="leading-snug"
                    v-html="
                      addCitations(
                        point,
                        commemoration.ai_bullet_points_citations
                      )
                    "
                  ></li>
                </ul>
              </el-card>
            </div>

            <div class="lg:w-2/3">
              <h3
                class="text-2xl font-bold mb-4 text-[var(--el-text-color-primary)] m-0 p-0 text-left"
              >
                {{ commemoration.name }}
              </h3>
              <div
                v-if="commemoration.ai_hagiography"
                class="prose dark:prose-invert max-w-none text-[var(--el-text-color-regular)]"
                v-html="
                  addCitations(
                    commemoration.ai_hagiography,
                    commemoration.ai_hagiography_citations
                  )
                "
              ></div>
            </div>
          </div>

          <div v-if="commemoration.ai_legend">
            <el-card
              shadow="never"
              class="border border-[var(--el-border-color-light)] bg-transparent"
            >
              <template #header>
                <div
                  class="font-bold text-lg text-[var(--el-text-color-primary)]"
                >
                  {{ commemoration.ai_legend_title }}:
                  <span
                    class="text-sm font-normal text-[var(--el-text-color-secondary)] block sm:inline sm:ml-2"
                  >
                    A Story from the Life of
                    {{ commemoration.saint_name || commemoration.name }}
                  </span>
                </div>
              </template>
              <div
                class="prose dark:prose-invert max-w-none text-[var(--el-text-color-regular)]"
                v-html="
                  addCitations(
                    commemoration.ai_legend,
                    commemoration.ai_legend_citations
                  )
                "
              ></div>
            </el-card>
          </div>

          <div
            v-if="commemoration.collect"
            class="bg-[var(--el-fill-color-light)] p-6 rounded-lg border border-[var(--el-border-color-light)]"
          >
            <h4
              class="text-sm font-bold uppercase tracking-wider mb-3 text-[var(--el-text-color-secondary)] m-0 p-0 text-left"
            >
              Collect
            </h4>
            <p
              class="text-lg leading-relaxed text-[var(--el-text-color-primary)] font-serif m-0"
            >
              {{ commemoration.collect }}
            </p>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div
              v-if="
                commemoration.ai_traditions &&
                commemoration.ai_traditions.length
              "
            >
              <el-card
                shadow="never"
                class="h-full border border-[var(--el-border-color-light)] bg-transparent"
              >
                <template #header>
                  <div
                    class="font-bold text-lg text-[var(--el-text-color-primary)]"
                  >
                    Traditions
                  </div>
                </template>
                <ul
                  class="space-y-3 list-disc pl-5 text-[var(--el-text-color-regular)] m-0"
                >
                  <li
                    v-for="(point, index) in commemoration.ai_traditions"
                    :key="index"
                    v-html="
                      addCitations(point, commemoration.ai_traditions_citations)
                    "
                  ></li>
                </ul>
              </el-card>
            </div>

            <div v-if="commemoration.ai_foods && commemoration.ai_foods.length">
              <el-card
                shadow="never"
                class="h-full border border-[var(--el-border-color-light)] bg-transparent"
              >
                <template #header>
                  <div
                    class="font-bold text-lg text-[var(--el-text-color-primary)]"
                  >
                    Foods
                  </div>
                </template>
                <ul
                  class="space-y-3 list-disc pl-5 text-[var(--el-text-color-regular)] m-0"
                >
                  <li
                    v-for="(point, index) in commemoration.ai_foods"
                    :key="index"
                    v-html="
                      addCitations(point, commemoration.ai_foods_citations)
                    "
                  ></li>
                </ul>
              </el-card>
            </div>
          </div>

          <el-alert
            type="success"
            :closable="false"
            class="border border-green-200 dark:border-green-900 bg-green-50 dark:bg-green-900/20 mt-8"
          >
            <template #title>
              <div class="text-center text-green-900 dark:text-green-100 py-2">
                <p
                  class="text-lg md:text-xl mb-3 font-serif italic leading-relaxed"
                >
                  "{{ commemoration.ai_verse }}"
                </p>
                <p
                  v-if="commemoration.ai_verse_citation"
                  class="text-sm font-semibold uppercase tracking-wider opacity-90 m-0"
                >
                  — {{ commemoration.ai_verse_citation }}
                </p>
              </div>
            </template>
          </el-alert>
        </div>
      </el-card>

      <Loading v-if="loading" class="mt-8" />

      <div v-if="error" class="mt-8 max-w-2xl mx-auto">
        <el-alert :title="error" type="error" :closable="false" show-icon />
      </div>
    </main>
  </div>
</template>

<script>
import Loading from '@/components/Loading.vue';
import { ref } from 'vue';
import DOMPurify from 'dompurify';
import { icon } from '@fortawesome/fontawesome-svg-core';
import { faArrowUpRightFromSquare } from '@fortawesome/pro-duotone-svg-icons';

export default {
  name: 'Commemoration',
  components: {
    Loading,
  },
  data() {
    return {
      commemoration: null,
      loading: true,
      error: null,
      activeName: ref('first'),
      linkIcon: icon(faArrowUpRightFromSquare).html[0],
      validImages: {
        ai_image_1: false,
        image_link: false,
      },
    };
  },
  async mounted() {
    await this.initialize();
  },
  methods: {
    async initialize() {
      this.loading = true;
      this.error = null;
      try {
        const commemoration = await this.$http.get(
          `${import.meta.env.VITE_API_URL}api/v1/commemorations/${this.$route.params.uuid}`
        );
        this.commemoration = commemoration.data;
        this.checkImages();
      } catch {
        this.error =
          'There was an error retrieving the commemoration. Please try again.';
        this.loading = false;
        return;
      }
      this.loading = false;
    },
    checkImages() {
      if (this.commemoration.ai_image_1) {
        this.validateImageUrl(this.commemoration.ai_image_1, 'ai_image_1');
      }
      if (this.commemoration.image_link) {
        this.validateImageUrl(this.commemoration.image_link, 'image_link');
      }
    },
    validateImageUrl(url, key) {
      const img = new window.Image();
      img.onload = () => {
        this.validImages[key] = true;
      };
      img.onerror = () => {
        this.validImages[key] = false;
      };
      img.src = url;
    },
    addCitations(text, citations) {
      if (!text || !citations) return text;

      let sanitizedText = DOMPurify.sanitize(text); // Removes any harmful scripts

      return sanitizedText.replace(/\[(\d+)\]/g, (match, index) => {
        index = parseInt(index, 10) - 1;
        if (index >= 0 && index < citations.length) {
          return `<sup class="inline-block ml-0.5"><a target="_blank" title="${citations[index]}" href="${citations[index]}" class="text-[var(--accent-color)] hover:opacity-80"> ${this.linkIcon} </a></sup>`;
        }
        return match;
      });
    },
  },
};
</script>

<style scoped>
[v-cloak] {
  display: none;
}

/* Base styles for prose content generated by AI */
:deep(.prose) {
  font-family: 'Adobe Caslon Pro', serif;
  font-size: var(--main-font-size, 1.125rem);
  line-height: var(--main-line-height, 1.7);
}

:deep(.prose p) {
  margin-bottom: 1.25em;
  margin-top: 0;
}

:deep(.prose h1),
:deep(.prose h2),
:deep(.prose h3),
:deep(.prose h4) {
  font-family: inherit;
  font-weight: 700;
  margin-top: 1.5em;
  margin-bottom: 0.5em;
}

:deep(.prose ul) {
  list-style-type: disc;
  padding-left: 1.5em;
  margin-bottom: 1.25em;
}

:deep(.prose li) {
  margin-bottom: 0.5em;
}

:deep(.prose a) {
  color: var(--accent-color);
  text-decoration: underline;
}

:deep(sup svg) {
  height: 0.8em;
  width: 0.8em;
  vertical-align: baseline;
}
</style>
