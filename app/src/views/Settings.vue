<template>
  <div class="settings-view">
    <Loading v-if="loading" />

    <main
      v-if="!loading"
      v-cloak
      class="max-w-6xl mx-auto pt-8 pb-12 px-4 lg:pb-16"
    >
      <header class="settings-hero">
        <h1 class="settings-hero__title">Settings</h1>
        <p class="settings-hero__description">
          Personalize prayer, readings, and display preferences in one place.
        </p>
      </header>

      <div class="settings-search-top">
        <label for="settings-global-search" class="settings-search-top__label">
          Search settings
        </label>
        <el-input
          id="settings-global-search"
          v-model="searchQuery"
          clearable
          class="settings-search-top__input"
          :placeholder="`Search display and ${openTabLabel} settings`"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
      <div v-if="isFiltering" class="settings-filter-banner" role="status">
        <span class="settings-filter-banner__text">
          Filter active: “{{ searchQuery.trim() }}”
        </span>
        <button
          type="button"
          class="settings-filter-banner__clear"
          @click="clearSearch"
        >
          Clear
        </button>
      </div>

      <el-tabs
        v-model="openTab"
        :tab-position="tabPosition"
        class="settings-tabs"
        @tab-change="toggleOffice"
      >
        <el-tab-pane label="Daily Office" name="office">
          <section class="settings-tab-stack">
            <div class="settings-display-narrow">
              <DisplaySettingsModule
                :search-query="searchQuery"
                context-label="Daily Office"
                :content-audio-enabled="dailyOfficeContentAudioEnabled"
              />
            </div>
            <SettingsPanel
              :available-settings="availableSettings"
              :search-query="searchQuery"
              site="Daily Office"
            />
          </section>
        </el-tab-pane>
        <el-tab-pane label="Family Prayer" name="family">
          <section class="settings-tab-stack">
            <div class="settings-display-narrow">
              <DisplaySettingsModule
                :search-query="searchQuery"
                context-label="Family Prayer"
                :content-audio-enabled="familyPrayerContentAudioEnabled"
              />
            </div>
            <SettingsPanel
              :available-settings="availableSettings"
              :search-query="searchQuery"
              site="Family Prayer"
            />
          </section>
        </el-tab-pane>
      </el-tabs>
      <DonationPrompt variant="long" />
    </main>
  </div>
</template>

<script>
import SettingsPanel from '@/components/SettingsPanel.vue';
import Loading from '@/components/Loading.vue';
import { DynamicStorage } from '@/helpers/storage';
import DonationPrompt from '@/components/DonationPrompt.vue';
import DisplaySettingsModule from '@/components/DisplaySettingsModule.vue';
import { Search } from '@element-plus/icons-vue';

export default {
  name: 'Settings',
  components: {
    SettingsPanel,
    Loading,
    DonationPrompt,
    DisplaySettingsModule,
    Search,
  },
  data() {
    return {
      availableSettings: null,
      loading: true,
      openTab: 'office',
      searchQuery: '',
      lastTrackedSearchTerm: '',
    };
  },
  computed: {
    tabPosition() {
      return 'top';
    },
    openTabLabel() {
      return this.openTab === 'family' ? 'Family Prayer' : 'Daily Office';
    },
    isFiltering() {
      return this.searchQuery.trim().length > 0;
    },
    dailyOfficeContentAudioEnabled() {
      return this.getSettingValue('reading_audio') === 'on';
    },
    familyPrayerContentAudioEnabled() {
      return this.getSettingValue('family_reading_audio') === 'on';
    },
  },
  watch: {
    searchQuery(value) {
      const normalized = value.trim().toLowerCase();
      if (normalized.length < 2 || normalized === this.lastTrackedSearchTerm) {
        return;
      }
      this.lastTrackedSearchTerm = normalized;
      this.trackSearch(normalized);
    },
  },
  async mounted() {
    await this.initialize();
  },
  methods: {
    getSettingValue(settingName) {
      const setting = this.availableSettings?.find(
        (item) => item.name === settingName
      );
      return setting?.active;
    },
    async initialize() {
      this.loading = true;
      this.availableSettings = this.$store.state.availableSettings || [];
      await this.$store.dispatch('initializeSettings');
      const settings = this.$store.state.settings || {};

      if (this.availableSettings) {
        this.availableSettings.forEach((setting, i) => {
          this.availableSettings[i].active = settings[setting.name];
        });
      }

      const storedPane = await DynamicStorage.getItem('settingsPane');
      if (storedPane) {
        this.openTab = storedPane;
      } else {
        await DynamicStorage.setItem('settingsPane', 'office');
      }

      this.loading = false;
    },
    async toggleOffice(value) {
      this.openTab = value;
      await DynamicStorage.setItem('settingsPane', value);
    },
    clearSearch() {
      this.searchQuery = '';
    },
    trackSearch(query) {
      if (!this.$gtag?.event) {
        return;
      }
      this.$gtag.event('settings_search_used', {
        site: this.openTabLabel,
        query_length: query.length,
      });
    },
  },
};
</script>

<style scoped>
[v-cloak] {
  display: none;
}

.settings-hero {
  margin-bottom: 1rem;
}

.settings-hero__title {
  margin: 0;
  font-size: clamp(1.85rem, 3.4vw, 2.45rem);
  line-height: 1.18;
  color: var(--el-text-color-primary);
}

.settings-hero__description {
  margin: 0.55rem 0 0;
  max-width: 62ch;
  color: var(--el-text-color-secondary);
  font-size: 0.97rem;
}

.settings-tabs {
  margin-bottom: 1rem;
}

.settings-tab-stack {
  padding-top: 0.25rem;
  display: grid;
  gap: 1rem;
}

.settings-display-narrow {
  width: min(100%, 58rem);
}

.settings-search-top {
  border: 1px solid var(--el-border-color-light);
  border-radius: 0.55rem;
  background-color: var(--el-fill-color-blank);
  padding: 0.58rem 0.66rem 0.66rem;
  margin-bottom: 0.7rem;
}

.settings-search-top__label {
  display: block;
  margin-bottom: 0.26rem;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--el-text-color-secondary);
}

.settings-filter-banner {
  margin-bottom: 0.9rem;
  border: 1px solid var(--accent-color);
  background-color: rgb(191 219 254 / 0.35);
  border-radius: 0.5rem;
  padding: 0.35rem 0.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.settings-filter-banner__text {
  color: var(--el-text-color-primary);
  font-size: 0.82rem;
  font-weight: 600;
}

.settings-filter-banner__clear {
  border: 1px solid var(--accent-color);
  background-color: var(--el-fill-color-blank);
  color: var(--accent-color);
  border-radius: 0.4rem;
  padding: 0.12rem 0.38rem;
  font-size: 0.74rem;
  font-weight: 700;
}

@media (max-width: 768px) {
  .settings-hero__description {
    font-size: 0.92rem;
  }

  .settings-tab-stack {
    gap: 0.85rem;
  }

  .settings-display-narrow {
    width: 100%;
  }
}
</style>
