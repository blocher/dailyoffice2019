<template>
  <div class="small-container">
    <h1>Psalms</h1>
    <h4>{{ selectedTopicName }}</h4>
    <Loading v-if="loading" />
    <el-alert v-if="error" :title="error" type="error" />
    <div v-if="!loading && !error">
      <div class="text-center">
        <el-select
          v-model="selectedTopic"
          class="w-full mb-8"
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
        <div class="flex justify-center full-width mb-4">
          <el-checkbox-group
            v-model="languageStyles"
            size="large"
            @change="handleLanguageChange"
          >
            <el-checkbox-button label="contemporary"
              >Contemporary</el-checkbox-button
            >
            <el-checkbox-button label="traditional"
              >Traditional</el-checkbox-button
            >
            <el-checkbox-button label="spanish">Spanish</el-checkbox-button>
          </el-checkbox-group>
        </div>
      </div>
      <div v-for="psalm in displayedPsalms" :key="psalm.number" class="mb-4">
        <p>
          <router-link :to="`/psalm/${psalm.number}`">
            <strong>{{ psalm.number }}</strong
            >&nbsp;
            <small>{{ psalm.latin_title }}</small>
          </router-link>
        </p>
        <div
          v-if="languageStyles.length > 0"
          class="psalm-list-multi-language"
          :style="{
            gridTemplateColumns: `repeat(${languageStyles.length}, 1fr)`,
          }"
        >
          <div
            v-for="style in languageStyles"
            :key="style"
            class="psalm-list-language-column"
          >
            <small
              v-if="style === 'contemporary' && psalm.verses[0]?.first_half"
            >
              {{ psalm.verses[0].first_half.replaceAll(/[^a-zA-Z]+$/gi, '') }}
            </small>
            <small
              v-if="style === 'traditional' && psalm.verses[0]?.first_half_tle"
            >
              {{
                psalm.verses[0].first_half_tle.replaceAll(/[^a-zA-Z]+$/gi, '')
              }}
            </small>
            <small
              v-if="style === 'spanish' && psalm.verses[0]?.first_half_spanish"
            >
              {{
                psalm.verses[0].first_half_spanish.replaceAll(
                  /[^a-zA-Z]+$/gi,
                  ''
                )
              }}
            </small>
          </div>
        </div>
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
      languageStyles: ['contemporary'],
    };
  },
  async created() {
    await this.loadLanguageStyle();
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
    this.error = false;
    this.loading = false;
  },
  watch: {
    '$route.path': {
      handler: async function (newPath) {
        // Reload language style when navigating to this route
        if (newPath === '/psalms') {
          await this.loadLanguageStyle();
        }
      },
      immediate: false,
    },
  },
  async activated() {
    // Reload language style when component becomes active (if using keep-alive)
    await this.loadLanguageStyle();
  },
  methods: {
    handleTagClick(topic_id) {
      this.selectedTopic = topic_id;
      this.updateDisplayedTopic();
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
    async loadLanguageStyle() {
      // Use the same storage key as the single psalm view
      const savedStylesStr = await DynamicStorage.getItem(
        'psalmLanguageStyles'
      );
      let savedStyles = null;

      // Try to parse as JSON array
      if (savedStylesStr && savedStylesStr !== '') {
        try {
          savedStyles = JSON.parse(savedStylesStr);
        } catch {
          // If parsing fails, treat as empty
          savedStyles = null;
        }
      }

      // If we have a valid array, use it
      if (Array.isArray(savedStyles) && savedStyles.length > 0) {
        const validStyles = savedStyles.filter((style) =>
          ['contemporary', 'traditional', 'spanish'].includes(style)
        );
        if (validStyles.length > 0) {
          this.languageStyles = validStyles;
          return; // Don't call setLanguageStyles here to avoid overwriting
        }
      }

      // Handle legacy single selection format
      const savedStyle = await DynamicStorage.getItem('psalmLanguageStyle');
      if (
        savedStyle === 'traditional' ||
        savedStyle === 'spanish' ||
        savedStyle === 'contemporary'
      ) {
        this.languageStyles = [savedStyle];
        // Migrate to new format
        await this.setLanguageStyles();
        return;
      }

      // Handle legacy 'traditionalPsalms' boolean
      const traditional = await DynamicStorage.getItem('traditionalPsalms');
      if (traditional === 'true' || traditional === true) {
        this.languageStyles = ['traditional'];
        // Migrate to new format
        await this.setLanguageStyles();
        return;
      }

      // Default to contemporary
      if (
        !Array.isArray(this.languageStyles) ||
        this.languageStyles.length === 0
      ) {
        this.languageStyles = ['contemporary'];
        await this.setLanguageStyles();
      }
    },
    handleLanguageChange() {
      // Ensure at least one language is selected
      if (this.languageStyles.length === 0) {
        this.languageStyles = ['contemporary'];
      }
      this.setLanguageStyles();
    },
    async setLanguageStyles() {
      // Ensure at least one language is selected
      if (
        !Array.isArray(this.languageStyles) ||
        this.languageStyles.length === 0
      ) {
        this.languageStyles = ['contemporary'];
      }
      // Stringify the array before saving
      await DynamicStorage.setItem(
        'psalmLanguageStyles',
        JSON.stringify(this.languageStyles)
      );
    },
  },
};
</script>

<style scoped>
.psalm-list-multi-language {
  display: grid;
  gap: 1rem;
  margin-top: 0.5rem;
  margin-bottom: 0.5rem;
}

.psalm-list-language-column {
  min-width: 0;
  font-size: 0.9em;
}

@media (max-width: 768px) {
  .psalm-list-multi-language {
    grid-template-columns: 1fr !important;
    gap: 0.5rem;
  }
}
</style>
