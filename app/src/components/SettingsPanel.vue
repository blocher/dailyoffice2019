<template>
  <div class="settings-panel">
    <p v-if="!groups.length && showEmpty" class="settings-empty">
      No settings match your search.
    </p>
    <section
      v-for="group in groups"
      :key="group.key"
      class="settings-group"
      :aria-labelledby="`settings-group-${group.key}`"
    >
      <h2 :id="`settings-group-${group.key}`" class="section-title">
        {{ group.label }}
      </h2>
      <div class="settings-group__list surface">
        <SettingRow
          v-for="setting in group.settings"
          :key="setting.uuid || setting.name"
          :setting="setting"
          :value="getActiveSettingValue(setting)"
          :open="isOpen(setting)"
          :saved="savedSettingName === setting.name"
          @update:open="(open) => toggleOpen(setting.name, open)"
          @change="(value) => onSettingChange(setting, value)"
        />
      </div>
    </section>
  </div>
</template>

<script>
import SettingRow from '@/components/SettingRow.vue';
import {
  SETTING_CATEGORIES,
  createNormalizedApiSetting,
  matchesSettingSearch,
} from '@/helpers/settingsUiMetadata';
import { toast } from '@/ui/feedback';

export default {
  name: 'SettingsPanel',
  components: {
    SettingRow,
  },
  props: {
    availableSettings: {
      type: Array,
      default: () => [],
    },
    site: {
      type: String,
      required: true,
    },
    searchQuery: {
      type: String,
      default: '',
    },
    // Off when the page shows other results (Display) for the search.
    showEmpty: {
      type: Boolean,
      default: true,
    },
    // A local copy of the settings to edit instead of the reader's own: the
    // panel then reads these and emits update:values, and never saves.
    values: {
      type: Object,
      default: null,
    },
  },
  emits: ['update:values'],
  data() {
    return {
      savedSettingName: '',
      savedSettingTimeoutId: null,
      openSettingName: '',
      saveRequestVersionBySetting: {},
      localActiveSettingValues: {},
    };
  },
  computed: {
    normalizedSettings() {
      return (this.availableSettings || [])
        .filter((setting) => setting.site_name === this.site)
        .map((setting) =>
          createNormalizedApiSetting(setting, (value) =>
            this.persistSettingChange(setting.name, value)
          )
        );
    },
    filteredSettings() {
      return this.normalizedSettings.filter((setting) =>
        matchesSettingSearch(setting, this.searchQuery)
      );
    },
    // Settings grouped by category, in the order the Settings page shows
    // them. Core (setting_type 1) settings lead within each group, then the
    // order set in the admin.
    groups() {
      const byCategory = new Map();
      for (const setting of this.filteredSettings) {
        if (!byCategory.has(setting.category)) {
          byCategory.set(setting.category, []);
        }
        byCategory.get(setting.category).push(setting);
      }
      const known = SETTING_CATEGORIES.map((c) => c.key);
      const unknown = [...byCategory.keys()]
        .filter((key) => !known.includes(key))
        .sort();
      return [...known, ...unknown]
        .filter((key) => byCategory.has(key))
        .map((key) => ({
          key,
          label: SETTING_CATEGORIES.find((c) => c.key === key)?.label || key,
          settings: byCategory
            .get(key)
            .slice()
            .sort(
              (a, b) =>
                (a.setting_type === 1 ? 0 : 1) -
                  (b.setting_type === 1 ? 0 : 1) ||
                (a.order ?? a.priority) - (b.order ?? b.priority)
            ),
        }));
    },
  },
  beforeUnmount() {
    if (this.savedSettingTimeoutId) {
      window.clearTimeout(this.savedSettingTimeoutId);
      this.savedSettingTimeoutId = null;
    }
  },
  methods: {
    // While searching, a handful of matches open themselves so the options
    // are visible without another tap.
    isOpen(setting) {
      if (this.openSettingName === setting.name) return true;
      return (
        Boolean(this.searchQuery.trim()) &&
        this.filteredSettings.length <= 3 &&
        this.openSettingName !== `!${setting.name}`
      );
    },
    toggleOpen(settingName, open) {
      if (!open && this.searchQuery.trim()) {
        this.openSettingName = `!${settingName}`;
        return;
      }
      this.openSettingName = open ? settingName : '';
    },
    async persistSettingChange(settingName, value) {
      const currentSettings = this.$store.state.settings || {};
      const updatedSettings = {
        ...currentSettings,
        [settingName]: value,
      };
      await this.$store.dispatch('saveSettings', updatedSettings);
    },
    getActiveSettingValue(setting) {
      if (this.values) {
        return this.values[setting.name] ?? setting.options?.[0]?.value;
      }
      if (
        Object.prototype.hasOwnProperty.call(
          this.localActiveSettingValues,
          setting.name
        )
      ) {
        return this.localActiveSettingValues[setting.name];
      }
      const storeValue = this.$store.state.settings?.[setting.name];
      if (storeValue !== undefined && storeValue !== null) {
        return storeValue;
      }
      return setting.active;
    },
    setActiveSettingValue(settingName, value) {
      this.localActiveSettingValues = {
        ...this.localActiveSettingValues,
        [settingName]: value,
      };
    },
    syncAvailableSettingActive(settingName, value) {
      const target = (this.availableSettings || []).find(
        (setting) => setting.name === settingName
      );
      if (target) {
        target.active = value;
      }
    },
    onSettingChange(setting, value) {
      if (this.values) {
        this.$emit('update:values', { ...this.values, [setting.name]: value });
        return;
      }
      const previousValue = this.getActiveSettingValue(setting);
      this.setActiveSettingValue(setting.name, value);
      this.syncAvailableSettingActive(setting.name, value);
      const requestVersion =
        (this.saveRequestVersionBySetting[setting.name] || 0) + 1;
      this.saveRequestVersionBySetting = {
        ...this.saveRequestVersionBySetting,
        [setting.name]: requestVersion,
      };

      setting
        .persist(value)
        .then(() => {
          if (
            this.saveRequestVersionBySetting[setting.name] !== requestVersion
          ) {
            return;
          }
          this.markSaved(setting.name);
          this.trackSettingChange(setting);
        })
        .catch(() => {
          if (
            this.saveRequestVersionBySetting[setting.name] !== requestVersion
          ) {
            return;
          }
          this.setActiveSettingValue(setting.name, previousValue);
          this.syncAvailableSettingActive(setting.name, previousValue);
          toast.error({
            title: 'That setting didn’t save',
            message: 'Please try again.',
          });
        });
    },
    markSaved(settingName) {
      this.savedSettingName = settingName;
      if (this.savedSettingTimeoutId) {
        window.clearTimeout(this.savedSettingTimeoutId);
      }
      this.savedSettingTimeoutId = window.setTimeout(() => {
        if (this.savedSettingName === settingName) {
          this.savedSettingName = '';
        }
      }, 1600);
    },
    trackSettingChange(setting) {
      if (!this.$gtag?.event) {
        return;
      }
      this.$gtag.event('settings_setting_changed', {
        site: this.site,
        setting_name: setting.name,
        setting_type: setting.setting_type,
      });
    },
  },
};
</script>

<style scoped>
.settings-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.settings-group .section-title {
  margin: 0 0 var(--space-2) var(--space-1);
}

.settings-group__list {
  overflow: hidden;
}

.settings-empty {
  padding: var(--space-6) 0;
  text-align: center;
  font-style: italic;
  color: var(--ink-faint);
}
</style>
