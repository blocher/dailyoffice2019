<template>
  <div class="small-container">
    <Loading v-if="loading" />
    <el-alert v-if="error" :title="error" type="error" />

    <header class="office-header mb-8">
      <h1 class="text-center">Psalms</h1>
      <h4 class="text-center">{{ selectedTopicName }}</h4>
      <div v-if="!loading && !error" class="space-y-6">
        <div
          class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-100 dark:border-gray-700 shadow-sm mt-6 mb-6"
        >
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h4
                class="text-sm font-semibold uppercase tracking-wider text-gray-500 mb-2"
              >
                Category
              </h4>
              <el-select
                v-model="selectedTopic"
                class="w-full"
                placeholder="Select"
                size="large"
                filterable
                @change="updateDisplayedTopic"
              >
                <el-option key="all" label="All Categories" value="all" />
                <el-option
                  v-for="topic in topics"
                  :key="topic.id"
                  :label="topic.topic_name"
                  :value="topic.id"
                />
              </el-select>
            </div>
            <div>
              <h4
                class="text-sm font-semibold uppercase tracking-wider text-gray-500 mb-2"
              >
                Language
              </h4>
              <div class="flex items-center h-[40px]">
                <el-switch
                  v-model="traditional"
                  size="large"
                  active-text="Traditional"
                  inactive-text="Contemporary"
                  @change="setTraditional"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>

    <div v-if="!loading && !error" id="main">
      <div
        v-for="psalm in displayedPsalms"
        :key="psalm.number"
        class="mb-4 bg-white dark:bg-gray-900 rounded-lg p-4 border border-gray-100 dark:border-gray-800 shadow-sm"
      >
        <div>
          <router-link
            :to="`/psalm/${psalm.number}`"
            class="text-lg font-semibold mb-1 block"
          >
            Psalm {{ psalm.number }}&nbsp;
            <small class="text-gray-500">{{ psalm.latin_title }}</small>
          </router-link>
          <small
            v-if="!traditional"
            class="text-gray-600 dark:text-gray-400 block mb-2"
            >{{ psalm.verses[0].first_half.replace(/[^\p{L}]+$/gu, '') }}</small
          >
          <small
            v-if="traditional"
            class="text-gray-600 dark:text-gray-400 block mb-2"
            >{{
              psalm.verses[0].first_half_tle.replace(/[^\p{L}]+$/gu, '')
            }}</small
          >
          <div class="mt-2">
            <el-tag
              v-for="topic in psalm.topics"
              :key="topic.id"
              class="mr-2 cursor-pointer"
              type="info"
              size="small"
              @click="handleTagClick(topic.id)"
            >
              {{ topic.topic_name }}
            </el-tag>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Loading from '@/components/Loading.vue';
import { DynamicStorage } from '@/helpers/storage';

export default {
  components: { Loading },
  data() {
    return {
      psalms: null,
      loading: true,
      error: false,
      topics: null,
      displayedPsalms: null,
      selectedTopic: 'all',
      selectedTopicName: 'All Categories',
      traditional: false,
    };
  },
  async created() {
    const traditional = await DynamicStorage.getItem(
      'traditionalPsalms',
      false
    );
    if (traditional == 'true' || traditional == true) {
      this.traditional = true;
    } else {
      this.traditional = false;
    }
    this.setTraditional();
    let data = null;
    try {
      data = await this.$http.get(
        `${import.meta.env.VITE_API_URL}api/v1/psalms`
      );
    } catch {
      this.error =
        'There was an error retrieving the psalms. Please try again.';
      this.loading = false;
      return;
    }
    this.psalms = data.data;
    this.displayedPsalms = this.psalms;

    try {
      data = await this.$http.get(
        `${import.meta.env.VITE_API_URL}api/v1/psalms/topics/`
      );
    } catch {
      this.error =
        'There was an error retrieving the psalms. Please try again.';
      this.loading = false;
      return;
    }
    this.topics = data.data;
    if (this.$route.query.topic) {
      const topicId = this.$route.query.topic;
      const t = this.topics.find((topic) => topic.id == topicId);
      if (t) {
        this.selectedTopic = t.id;
        this.updateDisplayedTopic();
      }
    }
    this.error = false;
    this.loading = false;
  },
  watch: {
    '$route.query.topic': function (newTopic) {
      if (newTopic && this.topics) {
        const t = this.topics.find((topic) => topic.id == newTopic);
        if (t) {
          this.selectedTopic = t.id;
          this.updateDisplayedTopic();
        }
      } else if (!newTopic && this.topics) {
        this.selectedTopic = 'all';
        this.updateDisplayedTopic();
      }
    },
  },
  methods: {
    handleTagClick(topic_id) {
      this.$router.push({ name: 'Psalms', query: { topic: topic_id } });
    },
    updateDisplayedTopic() {
      if (this.selectedTopic === 'all') {
        this.selectedTopicName = 'All Categories';
        this.displayedPsalms = this.psalms;
      } else {
        this.displayedPsalms = this.psalms.filter(
          (psalm) =>
            psalm.topics.map((topic) => topic.id).indexOf(this.selectedTopic) >
            -1
        );
        this.selectedTopicName = this.topics.find(
          (topic) => topic.id === this.selectedTopic
        ).topic_name;
      }
    },
    async setTraditional() {
      await DynamicStorage.setItem('traditionalPsalms', this.traditional);
    },
  },
};
</script>
