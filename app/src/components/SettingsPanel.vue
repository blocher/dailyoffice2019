<template>
  <section class="settings-panel">
    <section class="settings-section">
      <header class="settings-section__header">
        <div class="settings-section__title">Core Settings</div>
      </header>
      <p v-if="!coreSettings.length" class="settings-empty-state">
        No core settings match your search.
      </p>
      <div v-else class="settings-list">
        <article
          v-for="setting in coreSettings"
          :key="setting.uuid"
          class="setting-card setting-card--core"
        >
          <header class="setting-card__header">
            <div class="setting-card__copy">
              <div class="setting-card__title">{{ setting.title }}</div>
              <p
                v-if="getDescriptionPreview(setting)"
                class="setting-card__description"
              >
                {{ getDescriptionPreview(setting) }}
              </p>
              <button
                v-if="hasLongDescription(setting)"
                class="setting-card__details-toggle"
                type="button"
                @click="toggleDescription(setting.name)"
              >
                {{
                  isDescriptionExpanded(setting.name)
                    ? 'Hide details'
                    : 'Details'
                }}
              </button>
              <div
                v-if="isDescriptionExpanded(setting.name)"
                class="setting-card__details"
                v-html="setting.description"
              />
              <p v-if="setting.helpShort" class="setting-card__help">
                {{ setting.helpShort }}
              </p>
            </div>
            <span
              v-show="savedSettingName === setting.name"
              class="setting-card__saved"
            >
              Saved
            </span>
          </header>

          <div class="setting-options-shell">
            <RadioGroup
              :model-value="getActiveSettingValue(setting)"
              as="div"
              class="setting-options"
              @update:modelValue="(value) => onSettingChange(setting, value)"
            >
              <RadioGroupOption
                v-for="option in setting.options"
                :key="option.uuid || option.value"
                v-slot="{ checked, active }"
                as="template"
                :value="option.value"
              >
                <div :class="getOptionClasses(checked, active, false)">
                  <span
                    :class="[
                      checked
                        ? 'setting-options__dot-shell--checked'
                        : 'setting-options__dot-shell--unchecked',
                      active ? 'setting-options__dot-shell--active' : '',
                      'setting-options__dot-shell',
                    ]"
                    aria-hidden="true"
                  >
                    <span class="setting-options__dot" />
                  </span>
                  <div class="setting-options__text">
                    <RadioGroupLabel as="span" class="setting-options__name">
                      {{ option.name }}
                    </RadioGroupLabel>
                    <div
                      class="setting-options__description"
                      v-html="option.description"
                    />
                  </div>
                </div>
              </RadioGroupOption>
            </RadioGroup>
          </div>
        </article>
      </div>
    </section>

    <section class="settings-section settings-section--secondary">
      <header class="settings-section__header">
        <div class="settings-section__title">More Options</div>
      </header>
      <p v-if="!moreSettings.length" class="settings-empty-state">
        No additional settings match your search.
      </p>
      <div v-else class="settings-list settings-list--secondary">
        <article
          v-for="setting in moreSettings"
          :key="setting.uuid"
          class="setting-card setting-card--secondary"
        >
          <header class="setting-card__header">
            <div class="setting-card__copy">
              <div class="setting-card__title setting-card__title--secondary">
                {{ setting.title }}
              </div>
              <p
                v-if="getDescriptionPreview(setting)"
                class="setting-card__description"
              >
                {{ getDescriptionPreview(setting) }}
              </p>
              <button
                v-if="hasLongDescription(setting)"
                class="setting-card__details-toggle"
                type="button"
                @click="toggleDescription(setting.name)"
              >
                {{
                  isDescriptionExpanded(setting.name)
                    ? 'Hide details'
                    : 'Details'
                }}
              </button>
              <div
                v-if="isDescriptionExpanded(setting.name)"
                class="setting-card__details"
                v-html="setting.description"
              />
              <p v-if="setting.helpShort" class="setting-card__help">
                {{ setting.helpShort }}
              </p>
            </div>
            <span
              v-show="savedSettingName === setting.name"
              class="setting-card__saved"
            >
              Saved
            </span>
          </header>

          <div class="setting-options-shell">
            <RadioGroup
              :model-value="getActiveSettingValue(setting)"
              as="div"
              class="setting-options"
              @update:modelValue="(value) => onSettingChange(setting, value)"
            >
              <RadioGroupOption
                v-for="option in setting.options"
                :key="option.uuid || option.value"
                v-slot="{ checked, active }"
                as="template"
                :value="option.value"
              >
                <div :class="getOptionClasses(checked, active, true)">
                  <span
                    :class="[
                      checked
                        ? 'setting-options__dot-shell--checked'
                        : 'setting-options__dot-shell--unchecked',
                      active ? 'setting-options__dot-shell--active' : '',
                      'setting-options__dot-shell',
                    ]"
                    aria-hidden="true"
                  >
                    <span class="setting-options__dot" />
                  </span>
                  <div class="setting-options__text">
                    <RadioGroupLabel as="span" class="setting-options__name">
                      {{ option.name }}
                    </RadioGroupLabel>
                    <div
                      class="setting-options__description"
                      v-html="option.description"
                    />
                  </div>
                </div>
              </RadioGroupOption>
            </RadioGroup>
          </div>
        </article>
      </div>
    </section>
  </section>
</template>

<script>
import { RadioGroup, RadioGroupLabel, RadioGroupOption } from '@headlessui/vue';
import { ElMessage } from 'element-plus';
import {
  createNormalizedApiSetting,
  matchesSettingSearch,
} from '@/helpers/settingsUiMetadata';
import { getMessageOffset } from '@/helpers/getMessageOffest';

export default {
  name: 'SettingsPanel',
  components: {
    RadioGroup,
    RadioGroupLabel,
    RadioGroupOption,
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
  },
  data() {
    return {
      savedSettingName: '',
      savedSettingTimeoutId: null,
      expandedDescriptions: {},
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
    coreSettings() {
      return this.filteredSettings.filter(
        (setting) => setting.setting_type === 1
      );
    },
    moreSettings() {
      return this.filteredSettings.filter(
        (setting) => setting.setting_type !== 1
      );
    },
  },
  beforeUnmount() {
    if (this.savedSettingTimeoutId) {
      window.clearTimeout(this.savedSettingTimeoutId);
      this.savedSettingTimeoutId = null;
    }
  },
  methods: {
    sanitizeDescription(description) {
      return String(description || '')
        .replace(/<[^>]*>/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();
    },
    getDescriptionPreview(setting) {
      const text = this.sanitizeDescription(setting.description);
      if (!text) {
        return '';
      }
      if (text.length <= 160) {
        return text;
      }
      return `${text.slice(0, 157).trimEnd()}...`;
    },
    hasLongDescription(setting) {
      return this.sanitizeDescription(setting.description).length > 160;
    },
    toggleDescription(settingName) {
      this.expandedDescriptions = {
        ...this.expandedDescriptions,
        [settingName]: !this.expandedDescriptions[settingName],
      };
    },
    isDescriptionExpanded(settingName) {
      return Boolean(this.expandedDescriptions[settingName]);
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
          ElMessage.error({
            title: 'Save Failed',
            message: 'Unable to save this setting. Please try again.',
            showClose: true,
            offset: getMessageOffset(),
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
      }, 1200);
    },
    getOptionClasses(checked, active, secondary) {
      return [
        checked
          ? 'setting-options__choice--selected'
          : secondary
            ? 'setting-options__choice--secondary'
            : 'setting-options__choice--default',
        active ? 'setting-options__choice--active' : '',
        'setting-options__choice',
      ];
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
  margin-top: 0.42rem;
  display: grid;
  gap: 1rem;
  text-align: left;
}

.settings-section {
  margin-top: 0;
  border: 1px solid var(--el-border-color-light);
  border-radius: 0.56rem;
  background-color: var(--el-fill-color-blank);
  padding: 0.72rem;
}

.settings-section--secondary {
  margin-top: 0;
  background-color: var(--el-fill-color-light);
  border-color: var(--el-border-color-lighter);
}

.settings-section__header {
  margin-bottom: 0.36rem;
}

.settings-section__title {
  margin: 0;
  font-size: 1rem;
  line-height: 1.22;
  color: var(--el-text-color-primary);
  font-weight: 700;
}

.settings-empty-state {
  margin: 0.35rem 0 0;
  color: var(--el-text-color-secondary);
  font-size: 0.8rem;
}

.settings-list {
  margin-top: 0.78rem;
  display: grid;
  gap: 0.58rem;
}

.settings-list--secondary {
  gap: 0.52rem;
}

.setting-card {
  border-radius: 0.52rem;
  border: 1px solid var(--el-border-color-light);
  margin: 0;
  overflow: hidden;
}

.setting-card--core {
  background-color: var(--el-fill-color-blank);
  border-color: rgb(99 102 241 / 0.24);
  box-shadow: 0 1px 0 rgb(99 102 241 / 0.08);
}

.setting-card--secondary {
  background-color: var(--el-fill-color-light);
  border-color: var(--el-border-color-lighter);
  opacity: 0.96;
}

.setting-card--secondary .setting-card__header {
  padding: 0.52rem 3.25rem 0.26rem 0.6rem;
}

.setting-card__header {
  position: relative;
  display: flex;
  justify-content: space-between;
  gap: 0.44rem;
  align-items: flex-start;
  padding: 0.62rem 3.45rem 0.34rem 0.72rem;
}

.setting-card__copy {
  min-width: 0;
  width: 100%;
}

.setting-card__title {
  margin: 0;
  font-size: 0.88rem;
  line-height: 1.22;
  font-weight: 600;
  color: var(--el-text-color-primary);
  text-align: left;
}

.setting-card__title--secondary {
  font-size: 0.76rem;
  font-weight: 500;
  color: var(--el-text-color-regular);
}

.setting-card--secondary .setting-card__description {
  margin-top: 0.2rem;
  font-size: 0.71rem;
  line-height: 1.25;
}

.setting-card__description {
  margin: 0.24rem 0 0;
  font-size: 0.75rem;
  line-height: 1.3;
  color: var(--el-text-color-secondary);
  text-align: left;
}

.setting-card__details-toggle {
  margin-top: 0.2rem;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--accent-color);
  font-size: 0.72rem;
  font-weight: 600;
  text-decoration: underline;
  text-underline-offset: 2px;
  cursor: pointer;
}

.setting-card--secondary .setting-card__details-toggle {
  font-size: 0.69rem;
}

.setting-card__details {
  margin-top: 0.22rem;
  font-size: 0.74rem;
  color: var(--el-text-color-secondary);
  line-height: 1.28;
  text-align: left;
}

.setting-card--secondary .setting-card__details {
  font-size: 0.7rem;
}

.setting-card__details :deep(*) {
  margin: 0;
  padding: 0;
  margin-left: 0 !important;
  padding-left: 0 !important;
  text-indent: 0 !important;
}

.setting-card__details :deep(p + p) {
  margin-top: 0.24rem;
}

.setting-card__details :deep(ul),
.setting-card__details :deep(ol) {
  margin-top: 0.24rem;
  padding-left: 1rem !important;
}

.setting-card__help {
  margin: 0.2rem 0 0;
  font-size: 0.72rem;
  color: var(--el-text-color-secondary);
  text-align: left;
}

.setting-card--secondary .setting-card__help {
  font-size: 0.68rem;
}

.setting-card__saved {
  position: absolute;
  top: 0.54rem;
  right: 0.66rem;
  z-index: 1;
  pointer-events: none;
  flex-shrink: 0;
  border: 1px solid rgb(5 150 105 / 0.45);
  color: rgb(5 150 105);
  background-color: rgb(209 250 229 / 0.45);
  border-radius: 0.3rem;
  font-size: 0.64rem;
  font-weight: 700;
  padding: 0.13rem 0.28rem;
}

.setting-options-shell {
  border-top: 1px solid var(--el-border-color-light);
  padding: 0.58rem 0.68rem 0.7rem;
}

.setting-options {
  padding: 0;
  display: grid;
  gap: 0;
}

.setting-options__choice + .setting-options__choice {
  margin-top: 0.54rem;
}

.setting-card--core .setting-options-shell {
  background-color: rgb(99 102 241 / 0.03);
}

.setting-card--secondary .setting-options-shell {
  background-color: rgb(148 163 184 / 0.05);
  padding: 0.4rem 0.5rem 0.5rem;
}

.setting-options__choice {
  display: flex;
  align-items: flex-start;
  gap: 0.42rem;
  border: 1px solid var(--el-border-color);
  border-radius: 0.42rem;
  cursor: pointer;
  padding: 0.56rem 0.62rem;
  transition:
    border-color 0.14s ease,
    background-color 0.14s ease;
  text-align: left;
}

.setting-options__choice--default {
  background-color: var(--el-fill-color-blank);
}

.setting-options__choice--secondary {
  background-color: rgb(255 255 255 / 0.56);
}

.setting-card--secondary .setting-options__choice {
  padding: 0.34rem 0.42rem;
  border-color: var(--el-border-color-lighter);
}

.setting-card--secondary .setting-options__choice + .setting-options__choice {
  margin-top: 0.28rem;
}

:deep(.dark) .setting-options__choice--secondary {
  background-color: rgb(30 41 59 / 0.6);
}

.setting-options__choice--selected {
  border-color: var(--accent-color);
  background-color: rgb(191 219 254 / 0.2);
}

:deep(.dark) .setting-options__choice--selected {
  background-color: rgb(30 64 175 / 0.2);
}

.setting-options__choice--active {
  box-shadow: 0 0 0 2px rgb(59 130 246 / 0.12);
}

.setting-options__dot-shell {
  margin-top: 0.1rem;
  width: 0.82rem;
  height: 0.82rem;
  border-radius: 9999px;
  border: 1px solid var(--el-border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.setting-options__dot-shell--checked {
  border-color: var(--accent-color);
  background-color: var(--accent-color);
}

.setting-options__dot-shell--unchecked {
  background-color: var(--el-fill-color-blank);
}

.setting-options__dot-shell--active {
  box-shadow: 0 0 0 2px rgb(59 130 246 / 0.18);
}

.setting-options__dot {
  width: 0.28rem;
  height: 0.28rem;
  border-radius: 9999px;
  background-color: #fff;
}

.setting-options__text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.setting-options__name {
  color: var(--el-text-color-primary);
  font-size: 0.8rem;
  font-weight: 600;
  line-height: 1.2;
  text-align: left;
}

.setting-card--secondary .setting-options__name {
  font-size: 0.72rem;
  font-weight: 500;
}

.setting-options__description {
  margin-top: 0.14rem;
  color: var(--el-text-color-secondary);
  font-size: 0.75rem;
  line-height: 1.28;
  text-align: left;
}

.setting-options__description :deep(*) {
  margin: 0;
  padding: 0;
  margin-left: 0 !important;
  padding-left: 0 !important;
  text-indent: 0 !important;
}

.setting-options__description :deep(p + p) {
  margin-top: 0.2rem;
}

.setting-options__description :deep(ul),
.setting-options__description :deep(ol) {
  margin-top: 0.18rem;
  padding-left: 1rem !important;
}

.setting-card--secondary .setting-options__description {
  margin-top: 0.1rem;
  font-size: 0.68rem;
  line-height: 1.22;
}

@media (min-width: 1080px) {
  .settings-list--secondary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    column-gap: 0.66rem;
    row-gap: 0.56rem;
    align-items: start;
  }
}

@media (max-width: 768px) {
  .setting-card__header {
    padding: 0.56rem 3.02rem 0.3rem 0.58rem;
  }

  .setting-card--secondary .setting-card__header {
    padding: 0.46rem 2.82rem 0.24rem 0.52rem;
  }

  .setting-card__saved {
    top: 0.46rem;
    right: 0.5rem;
    font-size: 0.6rem;
  }

  .settings-section {
    padding: 0.58rem;
  }

  .setting-options-shell {
    padding: 0.48rem 0.56rem 0.58rem;
  }

  .setting-card--secondary .setting-options-shell {
    padding: 0.4rem 0.48rem 0.48rem;
  }

  .setting-options {
    gap: 0;
  }

  .setting-options__choice + .setting-options__choice {
    margin-top: 0.4rem;
  }

  .setting-card--secondary .setting-options__choice + .setting-options__choice {
    margin-top: 0.26rem;
  }
}
</style>
