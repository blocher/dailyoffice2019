<template>
  <div class="display-settings-shell">
    <div class="small-container">
      <div
        class="display-settings-summary mx-auto bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 shadow-xs p-3"
        role="button"
        tabindex="0"
        @click="openSettings"
        @keydown.enter.prevent="openSettings"
        @keydown.space.prevent="openSettings"
      >
        <div class="display-settings-summary__header">
          <div class="display-settings-summary__heading-row">
            <span class="display-settings-summary__heading"
              >Display Settings</span
            >
            <el-tag
              v-if="hasCustomDisplaySettings"
              type="warning"
              effect="plain"
              size="small"
              round
              >Custom</el-tag
            >
          </div>
          <span class="display-settings-summary__open">
            <font-awesome-icon :icon="['fad', 'right']" />
          </span>
        </div>
        <div
          class="display-settings-summary__text display-settings-summary__text--three-col"
        >
          <span class="display-settings-summary__item">
            <font-awesome-icon
              :icon="['fad', displayTheme === 'Dark' ? 'moon-stars' : 'sun']"
            />
            <span class="display-settings-summary__item-text">
              <span class="display-settings-summary__title">Theme</span>
              <span class="display-settings-summary__value">{{
                displayTheme
              }}</span>
            </span>
          </span>
          <span class="display-settings-summary__item">
            <font-awesome-icon :icon="['fad', 'font-case']" />
            <span class="display-settings-summary__item-text">
              <span class="display-settings-summary__title">Text Size</span>
              <span class="display-settings-summary__value"
                >{{ displayFontSizePercent }}%</span
              >
            </span>
          </span>
          <span class="display-settings-summary__item">
            <font-awesome-icon :icon="['fad', 'microphone']" />
            <span class="display-settings-summary__item-text">
              <span class="display-settings-summary__title"
                >Show Audio Controls</span
              >
              <span class="display-settings-summary__value">{{
                audioEnabledLocal ? 'On' : 'Off'
              }}</span>
            </span>
          </span>
        </div>
      </div>
    </div>
  </div>

  <el-drawer
    v-model="displaySettingsDrawerOpen"
    :direction="displaySettingsDrawerDirection"
    :size="displaySettingsDrawerSize"
    :with-header="false"
    :lock-scroll="false"
    class="display-settings-drawer"
  >
    <div class="display-settings-drawer__content">
      <div
        class="display-settings-drawer__row display-settings-drawer__header-row"
      >
        <div>
          <h3 class="display-settings-drawer__title">Display Settings</h3>
          <p class="display-settings-drawer__subtitle">
            Adjust appearance without leaving this page.
          </p>
        </div>
        <el-tag
          v-if="hasCustomDisplaySettings"
          type="warning"
          effect="plain"
          size="small"
          round
          >Custom</el-tag
        >
      </div>

      <div class="display-settings-drawer__row">
        <span class="display-settings-drawer__label">Appearance</span>
        <ThemeSwitcher />
      </div>

      <div class="display-settings-drawer__font">
        <span class="display-settings-drawer__label">Text Size</span>
        <FontSizer />
      </div>

      <div class="display-settings-drawer__row">
        <span class="display-settings-drawer__label"
          >Display Audio Controls</span
        >
        <el-switch
          v-model="audioEnabledLocal"
          size="default"
          active-text=""
          inactive-text=""
          inline-prompt
          :active-icon="checkIcon"
          :inactive-icon="closeIcon"
          style="--el-switch-on-color: var(--accent-color)"
        />
      </div>

      <el-button
        type="primary"
        class="display-settings-drawer__done"
        @click="closeSettings"
      >
        Done
      </el-button>
    </div>
  </el-drawer>
</template>

<script>
import FontSizer from '@/components/FontSizer.vue';
import ThemeSwitcher from '@/components/ThemeSwitcher.vue';
import { DynamicStorage } from '@/helpers/storage';
import { Check, Close } from '@element-plus/icons-vue';

export default {
  name: 'DisplaySettingsModule',
  components: {
    FontSizer,
    ThemeSwitcher,
  },
  emits: ['update:audioEnabled'],
  data() {
    return {
      displaySettingsDrawerOpen: false,
      displayTheme: 'Light',
      displayFontSize: 24,
      hasStoredThemePreference: false,
      windowWidth: 0,
      checkIcon: Check,
      closeIcon: Close,
      audioEnabledLocal: true,
    };
  },
  computed: {
    hasCustomDisplaySettings() {
      return (
        this.hasStoredThemePreference ||
        this.displayFontSize !== 24 ||
        !this.audioEnabledLocal
      );
    },
    displayFontSizePercent() {
      return this.getFontSizePercent(this.displayFontSize);
    },
    displaySettingsDrawerDirection() {
      return this.windowWidth < 768 ? 'btt' : 'rtl';
    },
    displaySettingsDrawerSize() {
      return this.windowWidth < 768 ? '72%' : '420px';
    },
  },
  watch: {
    async displaySettingsDrawerOpen(newVal) {
      if (!newVal) {
        await this.refreshDisplaySettingsSummary();
      }
    },
    async audioEnabledLocal(newVal) {
      await DynamicStorage.setItem('audioEnabled', newVal ? 'true' : 'false');
      this.$emit('update:audioEnabled', newVal);
    },
  },
  async mounted() {
    this.handleWindowResize();
    window.addEventListener('resize', this.handleWindowResize);
    await this.refreshDisplaySettingsSummary();
    const audioEnabledString = await DynamicStorage.getItem(
      'audioEnabled',
      'true'
    );
    this.audioEnabledLocal =
      audioEnabledString === 'true' ||
      audioEnabledString === true ||
      audioEnabledString === null ||
      audioEnabledString === undefined;

    // Emit initial value so parents sync up
    this.$emit('update:audioEnabled', this.audioEnabledLocal);
  },
  unmounted() {
    window.removeEventListener('resize', this.handleWindowResize);
  },
  methods: {
    openSettings() {
      this.displaySettingsDrawerOpen = true;
    },
    closeSettings() {
      this.displaySettingsDrawerOpen = false;
    },
    handleWindowResize() {
      this.windowWidth = window.innerWidth;
    },
    async refreshDisplaySettingsSummary() {
      const storedTheme = await DynamicStorage.getItem('user-theme');
      this.hasStoredThemePreference =
        storedTheme === 'light' || storedTheme === 'dark';
      this.displayTheme = this.getThemeLabel(storedTheme);

      const storedFontSize = parseInt(
        (await DynamicStorage.getItem('fontSize')) || '24',
        10
      );
      this.displayFontSize = Number.isNaN(storedFontSize) ? 24 : storedFontSize;
    },
    getThemeLabel(storedTheme) {
      const normalizedTheme =
        storedTheme === 'dark' || storedTheme === 'light'
          ? storedTheme
          : document.documentElement.classList.contains('dark')
            ? 'dark'
            : 'light';
      return normalizedTheme === 'dark' ? 'Dark' : 'Light';
    },
    getFontSizePercent(value) {
      const min = 10;
      const max = 40;
      if (max === min) {
        return 0;
      }
      const normalized = Math.min(max, Math.max(min, value));
      return Math.round(((normalized - min) / (max - min)) * 100);
    },
  },
};
</script>

<style scoped>
.display-settings-shell {
  margin-bottom: 1rem;
}

.display-settings-summary {
  width: 100%;
  max-width: 65ch;
  cursor: pointer;
  color: var(--el-text-color-primary);
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.display-settings-summary:hover {
  border-color: var(--accent-color);
  box-shadow: 0 2px 12px rgb(15 23 42 / 0.14);
}

.display-settings-summary:focus-visible {
  outline: 2px solid var(--accent-color);
  outline-offset: 2px;
}

.display-settings-summary__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.display-settings-summary__heading-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 0;
}

.display-settings-summary__heading {
  color: var(--el-text-color-regular);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.display-settings-summary__open {
  color: var(--el-text-color-regular);
  font-size: 0.85rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.display-settings-summary__text {
  margin-top: 0.45rem;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.35rem;
  width: 100%;
}

.display-settings-summary__item {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  width: 100%;
  min-width: 0;
}

.display-settings-summary__item :deep(svg) {
  flex-shrink: 0;
  color: var(--el-text-color-regular);
  font-size: 0.92rem;
}

.display-settings-summary__item-text {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.06rem;
  min-width: 0;
  text-align: center;
}

.display-settings-summary__title {
  color: var(--el-text-color-regular);
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.display-settings-summary__value {
  color: var(--el-text-color-primary);
  font-size: 0.88rem;
  font-weight: 600;
  white-space: nowrap;
}

.display-settings-drawer__content {
  padding: 0.25rem 0.25rem 1rem;
  color: var(--el-text-color-primary);
}

.display-settings-drawer__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.75rem 0;
  border-bottom: 1px solid var(--el-border-color-light);
}

.display-settings-drawer__header-row {
  align-items: flex-start;
  padding-top: 0;
}

.display-settings-drawer__title {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
}

.display-settings-drawer__subtitle {
  font-size: 0.85rem;
  color: var(--el-text-color-secondary);
  margin: 0.25rem 0 0;
}

.display-settings-drawer__label {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.display-settings-drawer__font {
  padding: 0.75rem 0;
  border-bottom: 1px solid var(--el-border-color-light);
}

.display-settings-drawer__done {
  width: 100%;
  margin-top: 1rem;
}

:deep(.dark) .display-settings-drawer__content {
  color: var(--el-text-color-primary);
}

:deep(.display-settings-drawer .font-size-block) {
  background-color: var(--el-fill-color) !important;
  border-color: var(--el-border-color-light) !important;
  box-shadow: none;
}

:deep(.display-settings-drawer .el-slider__button) {
  border-color: var(--accent-color);
}

:deep(.display-settings-drawer .el-slider__bar) {
  background-color: var(--accent-color);
}
</style>
