<template>
  <div class="page settings">
    <Loading v-if="loading" />

    <template v-else>
      <header class="page-header">
        <h1 class="page-title">Settings</h1>
        <p class="page-lede">
          Shape the offices to the way you pray. Changes save as you go.
        </p>
      </header>

      <div class="settings-search">
        <label for="settings-search" class="visually-hidden">
          Search settings
        </label>
        <UiInput
          id="settings-search"
          v-model="searchQuery"
          icon="search"
          clearable
          placeholder="Search settings — e.g. “psalter”, “litany”, “KJV”"
        />
      </div>

      <div class="settings-tabs">
        <UiSegmented
          :model-value="openTab"
          :options="tabs"
          variant="underline"
          block
          aria-label="Which settings to show"
          @update:model-value="toggleOffice"
        />
        <p class="settings-tabs__note">{{ tabNote }}</p>
      </div>

      <!-- Display: its own tab, and found by search from the other tabs -->
      <section
        v-if="isDisplayTab || (isFiltering && displayMatches)"
        class="settings-display"
        aria-labelledby="settings-display-title"
      >
        <h2
          v-if="!isDisplayTab"
          id="settings-display-title"
          class="section-title"
        >
          Display
        </h2>
        <h2 v-else id="settings-display-title" class="visually-hidden">
          Display
        </h2>
        <div class="surface settings-display__body">
          <DisplaySettings />
        </div>
      </section>

      <section
        v-if="!isDisplayTab"
        class="settings-offices"
        aria-label="Office settings"
      >
        <SettingsPanel
          :key="openTab"
          :available-settings="availableSettings"
          :search-query="searchQuery"
          :site="openTab === 'family' ? 'Family Prayer' : 'Daily Office'"
        />
      </section>

      <footer class="settings-footer">
        <UiButton v-if="!isDisplayTab" icon="share" @click="openPanel('share')">
          Share these settings
        </UiButton>
        <UiButton variant="ghost" icon="reset" @click="restoreDefaults">
          Restore defaults
        </UiButton>
      </footer>
    </template>
  </div>
</template>

<script>
import DisplaySettings from '@/components/DisplaySettings.vue';
import Loading from '@/components/Loading.vue';
import SettingsPanel from '@/components/SettingsPanel.vue';
import { resetDisplayPreferences } from '@/helpers/displayPreferences';
import { openPanel } from '@/helpers/panels';
import { DynamicStorage } from '@/helpers/storage';
import { confirm, toast } from '@/ui/feedback';

const DISPLAY_TERMS = [
  'display',
  'theme',
  'light',
  'dark',
  'sepia',
  'text',
  'size',
  'font',
  'typeface',
  'caslon',
  'garamond',
  'baskerville',
  'black letter',
  'gothic',
  'sans',
  'legible',
  'audio',
  'player',
  'rubric',
  'italic',
  'red',
  'contents',
  'margin',
  'sections',
];

export default {
  name: 'Settings',
  components: {
    DisplaySettings,
    Loading,
    SettingsPanel,
  },
  data() {
    return {
      availableSettings: null,
      loading: true,
      openTab: 'office',
      searchQuery: '',
      lastTrackedSearchTerm: '',
      tabs: [
        { value: 'office', label: 'Daily Office' },
        { value: 'family', label: 'Family Prayer' },
        { value: 'display', label: 'Display' },
      ],
    };
  },
  computed: {
    openTabLabel() {
      if (this.openTab === 'display') return 'Display';
      return this.openTab === 'family' ? 'Family Prayer' : 'Daily Office';
    },
    isDisplayTab() {
      return this.openTab === 'display';
    },
    isFiltering() {
      return Boolean(this.searchQuery.trim());
    },
    displayMatches() {
      const query = this.searchQuery.trim().toLowerCase();
      return DISPLAY_TERMS.some(
        (term) => term.includes(query) || query.includes(term)
      );
    },
    tabNote() {
      if (this.openTab === 'display') {
        return 'How the prayers look on this device. Also under Aa at the top of every page.';
      }
      return this.openTab === 'family'
        ? 'Short services for households and for children, from the Prayer Book’s Family Prayer.'
        : 'Morning, Midday, and Evening Prayer and Compline.';
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
    openPanel,
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
      if (['office', 'family', 'display'].includes(storedPane)) {
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
    async restoreDefaults() {
      if (this.isDisplayTab) {
        const ok = await confirm({
          title: 'Restore display defaults?',
          message:
            'Theme, text size, typeface, rubrics, margin contents, and the audio player go back to their defaults.',
          confirmText: 'Restore defaults',
          tone: 'danger',
        });
        if (!ok) return;
        await resetDisplayPreferences();
        toast.success('Display settings restored to their defaults.');
        return;
      }
      const site = this.openTabLabel;
      const ok = await confirm({
        title: `Restore ${site} defaults?`,
        message: `Every ${site} setting goes back to the Prayer Book’s default. Display settings are not affected.`,
        confirmText: 'Restore defaults',
        tone: 'danger',
      });
      if (!ok) return;
      const updated = { ...(this.$store.state.settings || {}) };
      (this.availableSettings || [])
        .filter((setting) => setting.site_name === site)
        .forEach((setting) => {
          const first = setting.options?.[0];
          if (first) {
            updated[setting.name] = first.value;
            setting.active = first.value;
          }
        });
      await this.$store.dispatch('saveSettings', updated);
      toast.success(`${site} settings restored to their defaults.`);
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
.settings {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.settings .page-header {
  margin-bottom: 0;
}

.settings-display .section-title {
  margin-left: var(--space-1);
}

.settings-display__body {
  padding: var(--space-5);
}

.settings-offices {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.settings-tabs__note {
  margin-top: var(--space-2);
  font-size: var(--text-sm);
  font-style: italic;
  text-align: center;
  color: var(--ink-faint);
}

.settings-footer {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--space-2);
  padding-top: var(--space-2);
}

@media (max-width: 559px) {
  .settings-display__body {
    padding: var(--space-4);
  }
}
</style>
