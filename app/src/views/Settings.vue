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

      <Transition name="settings-offline">
        <div v-if="!network.online" class="settings-offline">
          <UiIcon name="cloud-off" class="settings-offline__icon" />
          <div>
            <p class="settings-offline__title">You’re offline</p>
            <p class="settings-offline__text">
              Display settings work as always. Other settings change the offices
              themselves, so they wait for a connection, except choices already
              downloaded.
              <button
                type="button"
                class="settings-offline__link"
                @click="openPanel('offline')"
              >
                What’s downloaded
              </button>
            </p>
          </div>
        </div>
      </Transition>

      <button
        v-if="network.online"
        type="button"
        class="settings-offline-card"
        @click="openPanel('offline')"
      >
        <UiIcon :name="offlineIcon" class="settings-offline-card__icon" />
        <span class="settings-offline-card__copy">
          <span class="settings-offline-card__title">Offline</span>
          <span class="settings-offline-card__text">{{ offlineSummary }}</span>
        </span>
        <UiIcon name="chevron-right" class="settings-offline-card__chevron" />
      </button>

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

      <p
        v-if="isDisplayTab && isFiltering && !displayMatches"
        class="settings-empty"
      >
        No display settings match your search.
      </p>
      <p
        v-if="isFiltering && otherTabMatches.length"
        class="settings-elsewhere"
      >
        Also found in
        <template v-for="(match, index) in otherTabMatches" :key="match.value">
          <span v-if="index" aria-hidden="true"> · </span>
          <button
            type="button"
            class="settings-elsewhere__tab"
            @click="toggleOffice(match.value)"
          >
            {{ match.label
            }}<template v-if="match.count"> ({{ match.count }})</template>
          </button>
        </template>
      </p>

      <!-- Display: its own tab, and found by search from the other tabs -->
      <section
        v-if="isFiltering ? displayMatches : isDisplayTab"
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
          :key="`${openTab}-${panelVersion}`"
          :available-settings="availableSettings"
          :search-query="searchQuery"
          :show-empty="!(isFiltering && displayMatches)"
          :site="openTab === 'family' ? 'Family Prayer' : 'Daily Office'"
        />
      </section>

      <footer class="settings-footer">
        <UiButton v-if="!isDisplayTab" icon="share" @click="openPanel('share')">
          Share these settings
        </UiButton>
        <UiButton
          variant="ghost"
          icon="reset"
          :disabled="!isDisplayTab && !network.online"
          :title="
            !isDisplayTab && !network.online ? 'Needs a connection' : null
          "
          @click="restoreDefaults"
        >
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
import {
  createNormalizedApiSetting,
  matchesSettingSearch,
} from '@/helpers/settingsUiMetadata';
import { DynamicStorage } from '@/helpers/storage';
import { confirm, toast } from '@/ui/feedback';
import { effectiveDays, network, syncState } from '@/offline';
import { friendlyDate } from '@/offline/format';

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
      network,
      availableSettings: null,
      loading: true,
      openTab: 'office',
      searchQuery: '',
      lastTrackedSearchTerm: '',
      // Bumped to redraw the settings list after restoring defaults.
      panelVersion: 0,
      tabs: [
        { value: 'office', label: 'Daily Office' },
        { value: 'family', label: 'Family Prayer' },
        { value: 'display', label: 'Display' },
      ],
    };
  },
  computed: {
    offlineIcon() {
      if (effectiveDays() === 0) return 'cloud-off';
      return syncState.status === 'syncing' ? 'cloud-download' : 'cloud-check';
    },
    offlineSummary() {
      const days = effectiveDays();
      if (days === 0)
        return 'Downloads are off. Keep the days ahead on this device.';
      if (syncState.status === 'unavailable')
        return 'This browser can’t keep downloads (a private window, or blocked site data).';
      if (syncState.status === 'syncing') {
        return `Downloading the days ahead… ${syncState.done} of ${syncState.total}`;
      }
      if (syncState.readyThrough) {
        return `Ready offline through ${friendlyDate(syncState.readyThrough)} · ${days} days kept`;
      }
      return `Keeps ${days} days ahead on this device.`;
    },
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
    // While searching, the other tabs that also have matches.
    otherTabMatches() {
      const countFor = (site) =>
        (this.availableSettings || [])
          .filter((setting) => setting.site_name === site)
          .map((setting) => createNormalizedApiSetting(setting, () => {}))
          .filter((setting) => matchesSettingSearch(setting, this.searchQuery))
          .length;
      return (
        [
          {
            value: 'office',
            label: 'Daily Office',
            count: countFor('Daily Office'),
          },
          {
            value: 'family',
            label: 'Family Prayer',
            count: countFor('Family Prayer'),
          },
          {
            value: 'display',
            label: 'Display',
            count: this.displayMatches ? 1 : 0,
          },
        ]
          .filter((tab) => tab.value !== this.openTab && tab.count)
          // Display shows alongside the other tabs' results already.
          .filter((tab) => tab.value !== 'display' || this.isDisplayTab)
          .map((tab) => (tab.value === 'display' ? { ...tab, count: 0 } : tab))
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
      this.panelVersion += 1;
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
.settings-offline {
  display: flex;
  gap: var(--space-3);
  padding: var(--space-4);
  border: 1px solid var(--rule-strong);
  border-radius: var(--radius-lg);
  background-color: var(--paper-sunken);
}

.settings-offline__icon {
  flex-shrink: 0;
  margin-top: 0.15rem;
  font-size: var(--text-lg);
  color: var(--accent);
}

.settings-offline__title {
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
  font-size: var(--text-md);
  color: var(--ink);
}

.settings-offline__text {
  margin-top: var(--space-1);
  font-size: var(--text-sm);
  color: var(--ink-soft);
  line-height: 1.45;
}

.settings-offline__link {
  color: var(--accent);
  text-decoration: underline;
  text-underline-offset: 0.15em;
}

.settings-offline-enter-active,
.settings-offline-leave-active {
  transition: opacity 200ms var(--ease);
}

.settings-offline-enter-from,
.settings-offline-leave-to {
  opacity: 0;
}

/* The Offline panel, from Settings */
.settings-offline-card {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  width: 100%;
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--rule);
  border-radius: var(--radius-lg);
  background-color: var(--paper-raised);
  text-align: left;
  transition:
    border-color var(--duration) var(--ease),
    background-color var(--duration) var(--ease);
}

.settings-offline-card:hover {
  border-color: var(--rule-strong);
  background-color: var(--paper-sunken);
}

.settings-offline-card:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

.settings-offline-card__icon {
  flex-shrink: 0;
  font-size: var(--text-lg);
  color: var(--accent);
}

.settings-offline-card__copy {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: 0;
}

.settings-offline-card__title {
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
  color: var(--ink);
}

.settings-offline-card__text {
  font-size: var(--text-sm);
  font-style: italic;
  color: var(--ink-soft);
}

.settings-offline-card__chevron {
  flex-shrink: 0;
  color: var(--ink-faint);
}

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

.settings-elsewhere {
  margin-top: calc(-1 * var(--space-2));
  font-size: var(--text-sm);
  text-align: center;
  color: var(--ink-faint);
}

.settings-elsewhere__tab {
  min-height: 2.75rem;
  padding: 0 var(--space-1);
  color: var(--accent);
  text-decoration: underline;
  text-underline-offset: 0.15em;
}

.settings-empty {
  font-style: italic;
  text-align: center;
  color: var(--ink-faint);
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
