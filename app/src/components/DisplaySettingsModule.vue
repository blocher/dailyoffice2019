<template>
  <section class="display-settings-surface">
    <header class="display-settings-surface__header">
      <div class="display-settings-surface__title-shell">
        <p class="display-settings-surface__eyebrow">Display</p>
        <div class="display-settings-surface__title">Display Settings</div>
      </div>
      <el-tag
        v-if="hasCustomDisplaySettings"
        type="warning"
        effect="plain"
        size="small"
      >
        Custom
      </el-tag>
    </header>

    <p
      v-if="normalizedSearchQuery && !hasMatchingCards"
      class="display-settings-empty"
    >
      No display settings match your search.
    </p>

    <div v-else class="display-settings-grid">
      <article v-if="showAppearanceCard" class="display-setting-card">
        <header class="display-setting-card__header">
          <div class="display-setting-card__label">Appearance</div>
          <span>{{ displayTheme }}</span>
        </header>
        <div @change="scheduleSummaryRefresh" @click="scheduleSummaryRefresh">
          <ThemeSwitcher />
        </div>
      </article>

      <article v-if="showTextSizeCard" class="display-setting-card">
        <header class="display-setting-card__header">
          <div class="display-setting-card__label">Text Size</div>
          <span>{{ displayFontSizePercent }}%</span>
        </header>
        <FontSizer @font-size-change="handleFontSizeChange" />
      </article>

      <article v-if="showAudioControlsCard" class="display-setting-card">
        <header class="display-setting-card__header">
          <div class="display-setting-card__label">Show Audio Controls</div>
          <span>{{ audioEnabledLocal ? 'On' : 'Off' }}</span>
        </header>
        <div class="display-setting-card__switch-row">
          <el-switch
            v-model="audioEnabledLocal"
            size="default"
            style="--el-switch-on-color: var(--accent-color)"
          />
        </div>
        <!--        <p-->
        <!--          v-if="contentAudioEnabled"-->
        <!--          class="display-setting-card__dependency display-setting-card__dependency&#45;&#45;ok"-->
        <!--        >-->
        <!--          Reading audio is enabled for {{ contextLabel }}.-->
        <!--        </p>-->
        <!--        <p-->
        <!--          v-else-->
        <!--          class="display-setting-card__dependency display-setting-card__dependency&#45;&#45;warning"-->
        <!--        >-->
        <!--          Reading audio is off for {{ contextLabel }}.-->
        <!--        </p>-->
      </article>
    </div>
  </section>
</template>

<script>
import FontSizer from '@/components/FontSizer.vue';
import ThemeSwitcher from '@/components/ThemeSwitcher.vue';
import { DynamicStorage } from '@/helpers/storage';

export default {
  name: 'DisplaySettingsModule',
  components: {
    FontSizer,
    ThemeSwitcher,
  },
  emits: ['update:audioEnabled'],
  props: {
    contextLabel: {
      type: String,
      default: 'this service',
    },
    contentAudioEnabled: {
      type: Boolean,
      default: true,
    },
    searchQuery: {
      type: String,
      default: '',
    },
  },
  data() {
    return {
      displayTheme: 'Light',
      displayFontSize: 24,
      hasStoredThemePreference: false,
      audioEnabledLocal: true,
    };
  },
  computed: {
    normalizedSearchQuery() {
      return this.searchQuery.trim().toLowerCase();
    },
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
    showAppearanceCard() {
      return this.matchesDisplayCard([
        'display',
        'appearance',
        'theme',
        'light',
        'dark',
      ]);
    },
    showTextSizeCard() {
      return this.matchesDisplayCard([
        'display',
        'text',
        'size',
        'font',
        String(this.displayFontSizePercent),
      ]);
    },
    showAudioControlsCard() {
      return this.matchesDisplayCard([
        'display',
        'audio',
        'controls',
        this.contextLabel,
        this.contentAudioEnabled ? 'enabled' : 'disabled',
      ]);
    },
    hasMatchingCards() {
      return (
        this.showAppearanceCard ||
        this.showTextSizeCard ||
        this.showAudioControlsCard
      );
    },
  },
  watch: {
    async audioEnabledLocal(newVal) {
      await DynamicStorage.setItem('audioEnabled', newVal ? 'true' : 'false');
      this.$emit('update:audioEnabled', newVal);
    },
  },
  async mounted() {
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
    this.$emit('update:audioEnabled', this.audioEnabledLocal);
  },
  methods: {
    matchesDisplayCard(tokens) {
      if (!this.normalizedSearchQuery) {
        return true;
      }
      return tokens
        .join(' ')
        .toLowerCase()
        .includes(this.normalizedSearchQuery);
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
    handleFontSizeChange(value) {
      const fontSize = Number(value);
      if (Number.isNaN(fontSize)) {
        return;
      }
      this.displayFontSize = fontSize;
    },
    scheduleSummaryRefresh() {
      window.setTimeout(async () => {
        await this.refreshDisplaySettingsSummary();
      }, 0);
    },
  },
};
</script>

<style scoped>
.display-settings-surface {
  border: 1px solid var(--el-border-color-light);
  border-radius: 0.56rem;
  background-color: var(--el-fill-color-blank);
  padding: 0.72rem;
  width: min(100%, 52rem);
  margin-inline: auto;
}

.display-settings-surface__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.58rem;
}

.display-settings-surface__title-shell {
  min-width: 0;
}

.display-settings-surface__eyebrow {
  margin: 0;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--el-text-color-secondary);
}

.display-settings-surface__title {
  margin: 0.13rem 0 0;
  font-size: 1rem;
  font-weight: 700;
  line-height: 1.2;
  color: var(--el-text-color-primary);
}

.display-settings-empty {
  margin: 0.3rem 0 0;
  font-size: 0.82rem;
  color: var(--el-text-color-secondary);
}

.display-settings-grid {
  display: grid;
  gap: 0.6rem;
}

.display-setting-card {
  border: 1px solid var(--el-border-color-light);
  background-color: var(--el-fill-color-blank);
  border-radius: 0.46rem;
  padding: 0.58rem 0.62rem;
}

.display-setting-card__header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 0.56rem;
}

.display-setting-card__label {
  margin: 0;
  font-size: 0.8rem;
  font-weight: 600;
  line-height: 1.2;
  color: var(--el-text-color-primary);
}

.display-setting-card__header span {
  color: var(--el-text-color-secondary);
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.display-setting-card__switch-row {
  margin-top: 0.42rem;
}

.display-setting-card__dependency {
  margin: 0.48rem 0 0;
  font-size: 0.75rem;
}

.display-setting-card__dependency--ok {
  color: rgb(5 150 105);
}

.display-setting-card__dependency--warning {
  color: rgb(180 83 9);
}

:deep(.dark) .display-setting-card__dependency--ok {
  color: rgb(52 211 153);
}

:deep(.dark) .display-setting-card__dependency--warning {
  color: rgb(251 191 36);
}

@media (min-width: 768px) {
  .display-settings-surface {
    width: min(calc(100% - 1.25rem), 52rem);
  }
}
</style>
