<template>
  <div class="small-container">
    <Loading v-if="loading" />
    <el-alert v-if="error" :title="error" type="error" />

    <div v-if="loading || error">
      <h1 class="text-center">Psalm</h1>
    </div>

    <header v-if="!loading && !error" class="office-header mb-8">
      <h1 class="text-center mt-8">Psalm {{ psalm.number }}</h1>
      <h4 class="text-center">{{ psalm.latin_title }}</h4>
      <div
        v-if="psalm.topics && psalm.topics.length"
        class="text-center mt-2 mb-6"
      >
        <router-link
          v-for="topic in psalm.topics"
          :key="topic.id"
          :to="{ name: 'Psalms', query: { topic: topic.id } }"
        >
          <el-tag
            class="mr-2 cursor-pointer hover:opacity-80 transition-opacity"
            type="info"
            size="small"
          >
            {{ topic.topic_name }}
          </el-tag>
        </router-link>
      </div>
      <div class="space-y-6">
        <div
          class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-100 dark:border-gray-700 shadow-sm mt-6 mb-6"
        >
          <div
            class="flex flex-col md:flex-row justify-center md:justify-between items-center gap-4"
          >
            <h4
              class="text-sm font-semibold uppercase tracking-wider text-gray-500 mb-0"
            >
              Language
            </h4>
            <div class="flex items-center">
              <el-switch
                v-model="traditional"
                size="large"
                active-text="Traditional"
                inactive-text="Contemporary"
                @change="setTradtional"
              />
            </div>
          </div>
        </div>
      </div>
      <DisplaySettingsModule />
    </header>
  </div>

  <div v-if="!loading && !error" id="main" class="book-content">
    <!-- Top Navigation -->
    <div
      class="flex justify-between items-center mb-8 text-sm md:text-base font-medium text-gray-600 dark:text-gray-400"
    >
      <div class="flex-1 text-left">
        <router-link
          v-if="psalm.number > 1"
          :to="`/psalm/${psalm.number - 1}`"
          class="inline-flex items-center gap-2 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
        >
          <font-awesome-icon :icon="['fad', 'left']" />
          <span class="hidden sm:inline">Psalm</span> {{ psalm.number - 1 }}
        </router-link>
      </div>
      <div class="flex-1 text-center">
        <router-link
          :to="`/psalms/`"
          class="inline-block hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
        >
          All Psalms
        </router-link>
      </div>
      <div class="flex-1 text-right">
        <router-link
          v-if="psalm.number < 150"
          :to="`/psalm/${psalm.number + 1}`"
          class="inline-flex items-center gap-2 justify-end hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
        >
          <span class="hidden sm:inline">Psalm</span> {{ psalm.number + 1 }}
          <font-awesome-icon :icon="['fad', 'right']" />
        </router-link>
      </div>
    </div>

    <div v-if="!traditional">
      <span v-for="verse in psalm.verses" :key="verse.number">
        <span v-if="verse.first_half">
          <p class="hangingIndent extra-space-before">
            <sup>{{ verse.number }}</sup> {{ verse.first_half }} *
          </p>
          <p class="indent">
            {{ verse.second_half }}
          </p>
        </span>
      </span>
    </div>
    <div v-if="traditional">
      <span v-for="verse in psalm.verses" :key="verse.number">
        <span v-if="verse.first_half_tle">
          <p class="hangingIndent extra-space-before">
            <sup>{{ verse.number }}</sup> {{ verse.first_half_tle }} *
          </p>
          <p class="indent">
            {{ verse.second_half_tle }}
          </p>
        </span>
      </span>
    </div>
    <el-divider class="my-8" />
    <!-- Bottom Navigation -->
    <div
      class="flex justify-between items-center mt-8 mb-12 text-sm md:text-base font-medium text-gray-600 dark:text-gray-400"
    >
      <div class="flex-1 text-left">
        <router-link
          v-if="psalm.number > 1"
          :to="`/psalm/${psalm.number - 1}`"
          class="inline-flex items-center gap-2 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
        >
          <font-awesome-icon :icon="['fad', 'left']" />
          <span class="hidden sm:inline">Psalm</span> {{ psalm.number - 1 }}
        </router-link>
      </div>
      <div class="flex-1 text-center">
        <router-link
          :to="`/psalms/`"
          class="inline-block hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
        >
          All Psalms
        </router-link>
      </div>
      <div class="flex-1 text-right">
        <router-link
          v-if="psalm.number < 150"
          :to="`/psalm/${psalm.number + 1}`"
          class="inline-flex items-center gap-2 justify-end hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
        >
          <span class="hidden sm:inline">Psalm</span> {{ psalm.number + 1 }}
          <font-awesome-icon :icon="['fad', 'right']" />
        </router-link>
      </div>
    </div>
  </div>
</template>

<script>
import Loading from '@/components/Loading.vue';
import DisplaySettingsModule from '@/components/DisplaySettingsModule.vue';
import { DynamicStorage } from '@/helpers/storage';

export default {
  components: { Loading, DisplaySettingsModule },
  data() {
    return {
      psalm: null,
      loading: true,
      error: false,
      traditional: false,
    };
  },
  async created() {
    const traditional = await DynamicStorage.getItem(
      'traditionalPsalms',
      false
    );
    if (traditional === 'true' || traditional === true) {
      this.traditional = true;
    } else {
      this.traditional = false;
    }
    this.setTradtional();
    let data = null;
    try {
      data = await this.$http.get(
        `${import.meta.env.VITE_API_URL}api/v1/psalms/${this.$route.params.number}/`
      );
    } catch {
      this.error =
        'There was an error retrieving the psalms. Please try again.';
      this.loading = false;
      return;
    }
    this.psalm = data.data;
    this.error = false;
    this.loading = false;
  },
  methods: {
    async setTradtional() {
      await DynamicStorage.setItem('traditionalPsalms', this.traditional);
    },
  },
};
</script>
