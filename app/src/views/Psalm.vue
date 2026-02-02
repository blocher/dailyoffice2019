<template>
  <div class="small-container">
    <div v-if="!loading && !error">
      <h1>Psalm {{ psalm.number }}</h1>
      <h4>{{ psalm.latin_title }}</h4>
      <FontSizer />
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
    <div v-if="loading || error">
      <h1>Psalm</h1>
    </div>
    <Loading v-if="loading" />
    <el-alert v-if="error" :title="error" type="error" />
  </div>
  <div v-if="!loading && !error" id="main">
    <div
      v-if="languageStyles.length > 0"
      class="psalm-multi-language"
      :style="{ gridTemplateColumns: `repeat(${languageStyles.length}, 1fr)` }"
    >
      <div
        v-for="style in languageStyles"
        :key="style"
        class="psalm-language-column"
      >
        <h3 class="text-center mb-2">
          {{
            style === 'contemporary'
              ? 'Contemporary'
              : style === 'traditional'
                ? 'Traditional'
                : 'Spanish'
          }}
        </h3>
        <div v-if="style === 'contemporary'">
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
        <div v-if="style === 'traditional'">
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
        <div v-if="style === 'spanish'">
          <span v-for="verse in psalm.verses" :key="verse.number">
            <span v-if="verse.first_half_spanish">
              <p class="hangingIndent extra-space-before">
                <sup>{{ verse.number }}</sup> {{ verse.first_half_spanish }} *
              </p>
              <p class="indent">
                {{ verse.second_half_spanish }}
              </p>
            </span>
          </span>
        </div>
      </div>
    </div>
    <el-divider />
    <div class="mt-3">
      <router-link
        v-if="psalm.number > 1"
        class="float-left"
        :to="`/psalm/${psalm.number - 1}`"
      >
        <font-awesome-icon :icon="['fad', 'left']" />
        Psalm
        {{ psalm.number - 1 }}
      </router-link>

      <router-link
        v-if="psalm.number < 150"
        class="float-right"
        :to="`/psalm/${psalm.number + 1}`"
      >
        Psalm {{ psalm.number + 1 }}
        <font-awesome-icon :icon="['fad', 'right']" />
      </router-link>
      <br />
      <router-link
        v-if="psalm.number < 150"
        class="float-none content-center w-full"
        :to="`/psalms/`"
      >
        All Psalms
      </router-link>
    </div>
  </div>
</template>

<script>
import Loading from '@/components/Loading.vue';
import FontSizer from '@/components/FontSizer.vue';
import { DynamicStorage } from '@/helpers/storage';

export default {
  components: { Loading, FontSizer },
  data() {
    return {
      psalm: null,
      loading: true,
      error: false,
      languageStyles: ['contemporary'],
    };
  },
  async created() {
    await this.loadLanguageStyle();
    await this.loadPsalm();
  },
  async mounted() {
    // Ensure font size is applied after initial render
    await this.$nextTick();
    this.reapplyFontSize();
  },
  watch: {
    '$route.params.number': {
      handler: async function () {
        // Reload language styles from storage to ensure they persist
        await this.loadLanguageStyle();
        await this.loadPsalm();
      },
      immediate: false,
    },
    languageStyles: {
      handler: async function () {
        // Re-apply font size after language columns are rendered
        await this.$nextTick();
        this.reapplyFontSize();
      },
      deep: true,
    },
    psalm: {
      handler: async function () {
        // Re-apply font size after psalm data is loaded and columns are rendered
        await this.$nextTick();
        this.reapplyFontSize();
      },
      deep: true,
    },
  },
  methods: {
    async loadLanguageStyle() {
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

      if (Array.isArray(savedStyles) && savedStyles.length > 0) {
        // Validate that all saved styles are valid
        const validStyles = savedStyles.filter((style) =>
          ['contemporary', 'traditional', 'spanish'].includes(style)
        );
        if (validStyles.length > 0) {
          this.languageStyles = validStyles;
          return; // Don't call setLanguageStyles here to avoid overwriting
        }
      }

      // Handle legacy single selection
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

      // Default to contemporary if nothing found
      if (
        !Array.isArray(this.languageStyles) ||
        this.languageStyles.length === 0
      ) {
        this.languageStyles = ['contemporary'];
        await this.setLanguageStyles();
      }
    },
    async loadPsalm() {
      this.loading = true;
      this.error = false;
      let data = null;
      try {
        data = await this.$http.get(
          `${import.meta.env.VITE_API_URL}api/v1/psalms/${this.$route.params.number}/`
        );
        this.psalm = data.data;
        this.error = false;
      } catch {
        this.error =
          'There was an error retrieving the psalms. Please try again.';
      } finally {
        this.loading = false;
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
      // Stringify the array before saving (DynamicStorage converts to string anyway, but being explicit)
      await DynamicStorage.setItem(
        'psalmLanguageStyles',
        JSON.stringify(this.languageStyles)
      );
    },
    async reapplyFontSize() {
      // Re-apply font size to ensure all columns get the same size
      await this.$nextTick();
      const fontSize = parseInt(
        (await DynamicStorage.getItem('fontSize')) || '24'
      );
      const main = document.getElementById('main');
      if (main && fontSize) {
        // Apply to all elements that FontSizer would normally target
        const selectors = [
          '#main h2',
          '#main h3',
          '#main p',
          '#main .psalm-language-column h3',
          '#main .psalm-language-column p',
        ];
        selectors.forEach((selector) => {
          document.querySelectorAll(selector).forEach((el) => {
            el.style['font-size'] = `${fontSize}px`;
            if (
              el.tagName === 'P' ||
              el.tagName === 'H2' ||
              el.tagName === 'H3'
            ) {
              el.style['line-height'] = `${fontSize * 1.6}px`;
            }
          });
        });
      }
    },
  },
};
</script>

<style scoped>
.psalm-multi-language {
  display: grid;
  gap: 2rem;
  margin-bottom: 2rem;
}

.psalm-language-column {
  min-width: 0;
}

.psalm-language-column h3 {
  font-size: 1.1rem;
  font-weight: 600;
  color: #606266;
  border-bottom: 2px solid #e4e7ed;
  padding-bottom: 0.5rem;
  margin-bottom: 1rem;
}

@media (max-width: 768px) {
  .psalm-multi-language {
    grid-template-columns: 1fr !important;
    gap: 1.5rem;
  }
}
</style>
