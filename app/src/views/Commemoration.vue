<template>
  <div class="home">
    <el-container>
      <el-header v-if="!loading && commemoration">
        <h1>{{ commemoration.name }}</h1>
      </el-header>
      <el-main>
        <div style="max-width: 600px; margin: 0 auto">
          <el-alert type="warning" show-icon :closable="false">
            <template #title>
              <p>
                This is an <strong>experimental</strong> feature. The
                information is compiled from
                <strong>unofficial</strong> sources, and was built with
                assistance by AI. While we attempt to cite and link to all
                original sources, there may still be errors. Please report any
                factual or theological errors to
                <a href="mailto:feedback@dailyoffice2019.com"
                  >feedback@dailyoffice2019.com</a
                >
                for correction.
              </p>
            </template>
          </el-alert>
        </div>
        <el-card v-if="!loading && commemoration" class="commemoration-card">
          <template #header>
            <div class="card-header">
              <span>{{ commemoration.ai_one_sentence }}</span>
            </div>
          </template>

          <div v-if="commemoration.image_link" class="image-container">
            <el-image :src="commemoration.image_link" fit="contain" />
          </div>

          <div class="details">
            <el-alert type="success" :closable="false">
              <template #title>
                <p>
                  <strong
                    v-html="
                      addCitations(
                        commemoration.ai_quote,
                        commemoration.ai_quote_citations
                      )
                    "
                  ></strong>
                </p>
                <p v-if="commemoration.ai_quote_by">
                  <em>-- {{ commemoration.ai_quote_by }}</em>
                </p>
              </template>
            </el-alert>

            <div class="bullet-points-wrapper floating-box">
              <ul class="bullet-points">
                <li
                  v-for="(point, index) in commemoration.ai_bullet_points"
                  :key="index"
                  v-html="
                    addCitations(
                      point,
                      commemoration.ai_bullet_points_citations
                    )
                  "
                ></li>
              </ul>
            </div>

            <div class="text-content">
              <h3>{{ commemoration.name }}</h3>

              <div
                v-if="commemoration.ai_hagiography"
                v-html="
                  addCitations(
                    commemoration.ai_hagiography,
                    commemoration.ai_hagiography_citations
                  )
                "
              ></div>
            </div>

            <div v-if="commemoration.ai_legend">
              <el-card class="subcard">
                <template #header>
                  <div class="card-header">
                    <span>A Story from the Life</span>
                  </div>
                </template>
                <p
                  v-html="
                    addCitations(
                      commemoration.ai_legend,
                      commemoration.ai_legend_citations
                    )
                  "
                ></p>
              </el-card>
            </div>
            <div>
              <el-card class="subcard">
                <template #header>
                  <div class="card-header">
                    <span>Ecumenical Sources</span>
                  </div>
                </template>
                <el-tabs
                  v-model="activeName"
                  class="demo-tabs"
                  @tab-click="handleClick"
                >
                  <el-tab-pane
                    label="Lesser Feasts and Fasts, 2018 (Episcopal)"
                    name="first"
                  >
                    <p v-if="commemoration.ai_lesser_feasts_and_fasts">
                      {{ commemoration.ai_lesser_feasts_and_fasts }}
                    </p>
                    <p v-else>Not available.</p>
                  </el-tab-pane>
                  <el-tab-pane
                    label="Roman Martyrology (Catholic)"
                    name="second"
                  >
                    <p v-if="commemoration.ai_martyrology">
                      {{ commemoration.ai_martyrology }}
                    </p>
                    <p v-else>Not available.</p>
                  </el-tab-pane>
                  <el-tab-pane
                    label="Alban Butler's Lives of the Saints (Catholic)"
                    name="third"
                  >
                    <p v-if="commemoration.ai_butler">
                      {{ commemoration.ai_butler }}
                    </p>
                    <p v-else>Not available.</p>
                  </el-tab-pane>
                </el-tabs>
              </el-card>
            </div>
            <div v-if="commemoration.collect">
              <strong>Collect:</strong> {{ commemoration.collect }}
            </div>

            <div v-if="commemoration.ai_traditions">
              <el-card class="subcard">
                <template #header>
                  <div class="card-header">
                    <span>Traditions</span>
                  </div>
                </template>
                <ul class="bullet-points">
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

            <div v-if="commemoration.ai_foods">
              <el-card class="subcard">
                <template #header>
                  <div class="card-header">
                    <span>Foods</span>
                  </div>
                </template>
                <ul class="bullet-points">
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

            <el-alert type="success" :closable="false">
              <template #title>
                <p>
                  <strong>{{ commemoration.ai_verse }}</strong>
                </p>
                <p v-if="commemoration.ai_verse_citation">
                  <em>-- {{ commemoration.ai_verse_citation }}</em>
                </p>
              </template>
            </el-alert>
          </div>
        </el-card>
        <Loading v-if="loading" />
        <div v-if="error" class="error-message">
          <el-alert :title="error" type="error" :closable="false" />
        </div>
      </el-main>
    </el-container>
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
      } catch {
        this.error =
          'There was an error retrieving the commemoration. Please try again.';
        this.loading = false;
        return;
      }
      this.loading = false;
    },
    addCitations(text, citations) {
      if (!text || !citations) return text;

      let sanitizedText = DOMPurify.sanitize(text); // Removes any harmful scripts

      return sanitizedText.replace(/\[(\d+)\]/g, (match, index) => {
        index = parseInt(index, 10) - 1;
        if (index >= 0 && index < citations.length) {
          return `<sup><a target="_blank" title="${citations[index]}" href="${citations[index]}"> ${this.linkIcon} </a></sup>`;
        }
        return match;
      });
    },
  },
};
</script>

<style scoped>
h2,
h3,
h4 {
  text-align: left !important;
  padding-top: 10px;
}

.commemoration-card {
  width: 80%;
  margin: 20px auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.image-container {
  text-align: center;
  margin-bottom: 20px;
}

.details {
  margin-top: 20px;
}

.links-list {
  list-style-type: none;
  padding: 0;
}

.bullet-points {
  list-style-type: disc;
  padding-left: 20px;
}

.error-message {
  width: 80%;
  margin: 20px auto;
}

.el-alert {
  margin-bottom: 20px;
}

.bullet-points-wrapper {
  border: 1px solid #ccc;
  padding: 20px;
}

.bullet-points-wrapper li {
  margin-bottom: 10px;
  text-align: left;
}

.floating-box {
  float: left; /* or right */
  width: 33%;
  margin: 10px;
  background-color: lightblue;
  text-align: center;
  padding: 20px;
}

.subcard {
  margin-top: 20px;
  margin-bottom: 20px;
}
</style>
