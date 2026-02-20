<template>
  <div class="home office">
    <div class="small-container">
      <PageNotFound v-if="notFound" />
      <div v-if="!notFound" class="space-y-6">
        <Loading v-if="loading" />

        <!-- Header Section -->
        <header class="office-header mb-8">
          <CalendarCard
            :office="office"
            :calendar-date="calendarDate"
            :card="card"
            :service-type="serviceType"
          />
          <el-alert
            v-if="error"
            :title="error"
            type="error"
            show-icon
            class="my-4"
          />
          <OfficeNav
            :calendar-date="calendarDate"
            :selected-office="office"
            :service-type="serviceType"
          />

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
            <div class="display-settings-summary__text">
              <span class="display-settings-summary__item">
                <font-awesome-icon
                  :icon="[
                    'fad',
                    displayTheme === 'Dark' ? 'moon-stars' : 'sun',
                  ]"
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
                  <span class="display-settings-summary__title">Text</span>
                  <span class="display-settings-summary__value"
                    >{{ displayFontSizePercent }}%</span
                  >
                </span>
              </span>
              <span class="display-settings-summary__item">
                <font-awesome-icon :icon="['fad', 'microphone']" />
                <span class="display-settings-summary__item-text">
                  <span class="display-settings-summary__title">Audio</span>
                  <span class="display-settings-summary__value">{{
                    audioEnabled ? 'On' : 'Off'
                  }}</span>
                </span>
              </span>
            </div>
          </div>
        </header>
      </div>
    </div>

    <!-- Main Content (Book Style) -->
    <div id="main" class="book-content">
      <div v-for="module in modules" :key="module.name">
        <div v-for="line in module.lines" :key="line.content">
          <OfficeHeading v-if="line.line_type === 'heading'" :line="line" />
          <OfficeSubheading
            v-if="line.line_type === 'subheading'"
            :line="line"
          />
          <OfficeCitation v-if="line.line_type === 'citation'" :line="line" />
          <OfficeHTML
            v-if="line.line_type === 'html' || line.line_type === 'audio'"
            :line="line"
          />
          <OfficeLeader
            v-if="line.line_type === 'leader' || line.line_type === 'reader'"
            :line="line"
          />
          <OfficeLeaderDialogue
            v-if="line.line_type === 'leader_dialogue'"
            :line="line"
          />
          <OfficeCongregation
            v-if="line.line_type === 'congregation'"
            :line="line"
          />

          <OfficeCongregationDialogue
            v-if="line.line_type === 'congregation_dialogue'"
            :line="line"
          />

          <OfficeRubric v-if="line.line_type === 'rubric'" :line="line" />
          <OfficeSpacer v-if="line.line_type === 'spacer'" />
        </div>
      </div>
    </div>

    <!-- Footer Section -->
    <footer class="office-footer mt-12 pb-24">
      <!-- DonationPrompt removed to avoid duplication with App.vue footer -->
    </footer>
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
        <FontSizer v-if="readyToSetFontSize" />
        <p v-else class="display-settings-drawer__loading">
          Loading text size control...
        </p>
      </div>

      <div class="display-settings-drawer__row">
        <span class="display-settings-drawer__label">Audio Controls</span>
        <el-switch
          v-model="audioEnabled"
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

  <AudioPlayer
    v-if="
      !loading &&
      audioEnabled &&
      audioReady &&
      audioLinks &&
      audioLinks.length &&
      isWithinSevenDays &&
      isEsvOrKjv
    "
    :audio="audioLinks"
    :audioReady="audioReady"
    :office="office"
    :isEsvOrKjv="isEsvOrKjv"
    :isWithinSevenDays="isWithinSevenDays"
  />
  <AudioPlayerMessage
    v-if="
      !loading &&
      audioEnabled &&
      (!isWithinSevenDays ||
        !isEsvOrKjv ||
        !audioLinks ||
        !audioLinks.length ||
        !audioReady)
    "
    :isEsvOrKjv="isEsvOrKjv"
    :isWithinSevenDays="isWithinSevenDays"
    :audioReady="audioReady"
  />
</template>

<script>
// @ is an alias to /src
import OfficeHeading from '@/components/OfficeHeading.vue';
import OfficeSubheading from '@/components/OfficeSubheading.vue';
import OfficeCitation from '@/components/OfficeCitation.vue';
import OfficeHTML from '@/components/OfficeHTML.vue';
import OfficeCongregation from '@/components/OfficeCongregation.vue';
import OfficeLeader from '@/components/OfficeLeader.vue';
import OfficeCongregationDialogue from '@/components/OfficeCongregationDialogue.vue';
import OfficeLeaderDialogue from '@/components/OfficeLeaderDialogue.vue';
import OfficeRubric from '@/components/OfficeRubric.vue';
import OfficeSpacer from '@/components/OfficeSpacer.vue';
import Loading from '@/components/Loading.vue';
import CalendarCard from '@/components/CalendarCard.vue';
import OfficeNav from '@/components/OfficeNav.vue';
import PageNotFound from '@/views/PageNotFound.vue';
import FontSizer from '@/components/FontSizer.vue';
import { DynamicStorage } from '@/helpers/storage';
import AudioPlayer from '@/components/AudioPlayer.vue';
import AudioPlayerMessage from '@/components/AudoPlayerMessage.vue';
import ThemeSwitcher from '@/components/ThemeSwitcher.vue';
import { Check, Close } from '@element-plus/icons-vue';
import { resolveColorFromCard, setSeasonAccent } from '@/helpers/seasonAccent';

export default {
  name: 'Office',
  components: {
    AudioPlayerMessage,
    AudioPlayer,
    OfficeHeading,
    OfficeSubheading,
    OfficeCitation,
    OfficeHTML,
    OfficeCongregation,
    OfficeLeader,
    OfficeCongregationDialogue,
    OfficeLeaderDialogue,
    OfficeRubric,
    OfficeSpacer,
    Loading,
    CalendarCard,
    OfficeNav,
    PageNotFound,
    FontSizer,
    ThemeSwitcher,
  },
  props: {
    office: {
      type: String,
    },
    calendarDate: {
      type: Date,
    },
    serviceType: {
      default: 'office',
      type: String,
    },
  },
  data() {
    return {
      counter: 0,
      modules: null,
      loading: true,
      readyToSetFontSize: false,
      error: false,
      card: '',
      notFound: false,
      audioLinks: [],
      audioReady: false,
      audioEnabled: true,
      isEsvOrKjv: false,
      checkIcon: Check,
      closeIcon: Close,
      displaySettingsDrawerOpen: false,
      displayTheme: 'Light',
      displayFontSize: 24,
      hasStoredThemePreference: false,
      windowWidth: 0,
    };
  },
  computed: {
    isWithinSevenDays() {
      const today = new Date();
      const yesterday = new Date(today);
      yesterday.setDate(today.getDate() - 3);
      const sevenDaysFromNow = new Date(today);
      sevenDaysFromNow.setDate(today.getDate() + 9);

      return (
        this.calendarDate >= yesterday && this.calendarDate <= sevenDaysFromNow
      );
    },
    hasCustomDisplaySettings() {
      return (
        this.hasStoredThemePreference ||
        this.displayFontSize !== 24 ||
        !this.audioEnabled
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
    async audioEnabled(newVal) {
      await DynamicStorage.setItem('audioEnabled', newVal ? 'true' : 'false');
    },
    async displaySettingsDrawerOpen(newVal) {
      if (!newVal) {
        await this.refreshDisplaySettingsSummary();
      }
    },
  },
  async mounted() {
    this.handleWindowResize();
    window.addEventListener('resize', this.handleWindowResize);
    await DynamicStorage.setItem('serviceType', 'office');
    const audioEnabledString = await DynamicStorage.getItem(
      'audioEnabled',
      'true'
    );
    const audioEnabled =
      audioEnabledString === 'true' ||
      audioEnabledString === true ||
      audioEnabledString === null ||
      audioEnabledString === undefined;
    this.audioEnabled = audioEnabled;
    await this.initializeThemePreference();
    await this.initializeSettingsDrawer();
    await this.refreshDisplaySettingsSummary();
  },
  unmounted() {
    window.removeEventListener('resize', this.handleWindowResize);
  },

  async created() {
    const valid_daily_offices = [
      'morning_prayer',
      'midday_prayer',
      'evening_prayer',
      'compline',
    ];
    const valid_family_offices = [
      'morning_prayer',
      'midday_prayer',
      'early_evening_prayer',
      'close_of_day_prayer',
    ];
    const valid_offices =
      this.serviceType == 'office' ? valid_daily_offices : valid_family_offices;
    if (!valid_offices.includes(this.$props.office)) {
      this.notFound = true;
      return;
    }
    const today_str =
      this.calendarDate.getFullYear() +
      '-' +
      (this.calendarDate.getMonth() + 1) +
      '-' +
      this.calendarDate.getDate();
    this.availableSettings = await this.$store.state.availableSettings;
    await this.$store.dispatch('initializeSettings');
    const settings = await this.$store.state.settings;
    if (
      !Object.prototype.hasOwnProperty.call(settings, 'bible_translation') ||
      !settings.bible_translation
    ) {
      settings.bible_translation = 'esv';
    }
    this.isEsvOrKjv = ['esv', 'kjv'].includes(settings.bible_translation);
    const queryString = Object.keys(settings)
      .map((key) => key + '=' + settings[key])
      .join('&');
    let data = null;
    const office_url =
      `${import.meta.env.VITE_API_URL}api/v1/${this.serviceType}/${this.office}/` +
      today_str +
      '?' +
      queryString +
      '&extra_collects=' +
      (await this.extraCollects());
    try {
      data = await this.$http.get(office_url);
    } catch {
      this.error =
        'There was an error retrieving the office. Please try again.';
      this.loading = false;
      return;
    }
    this.modules = data.data.modules;
    this.card = data.data.calendar_day;
    this.applySeasonAccentFromCard(this.card);
    this.error = false;
    this.loading = false;
    await this.$nextTick();
    this.readyToSetFontSize = true;
    if (this.isEsvOrKjv) {
      this.audioLinks = await this.setAudioLinks(office_url);
    }
    this.audioReady = true;
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
    async initializeSettingsDrawer() {
      this.displaySettingsDrawerOpen = false;
      await DynamicStorage.deleteItem('displaySettingsDrawerSeen');
      await DynamicStorage.setItem('displaySettingsDrawerOpen', 'false');
    },
    async initializeThemePreference() {
      let activeTheme = await DynamicStorage.getItem('user-theme');
      if (!activeTheme) {
        const hasDarkPreference = window.matchMedia(
          '(prefers-color-scheme: dark)'
        ).matches;
        activeTheme = hasDarkPreference ? 'dark' : 'light';
      }
      document.documentElement.className = activeTheme;
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
    applySeasonAccentFromCard(card) {
      const liturgicalColor = resolveColorFromCard(card, this.office);
      if (liturgicalColor) {
        setSeasonAccent(liturgicalColor);
      }
    },
    async setAudioLinks(url) {
      url = `${url}&include_audio_links=true`;
      try {
        const data = await this.$http.get(url);
        this.audioLinks = data.data.audio.single_track;
        return data.data.audio.single_track;
      } catch {
        return [];
      }
    },
    async setAudioLinksBak() {
      const audio_links = [];
      for (const module of this.modules) {
        audio_links.push(...(await this.getAudioLinksForModule(module)));
      }
      return audio_links;
    },
    async getAudioLinksForModule(module) {
      const links = [];
      for (const line of module.lines) {
        const url = await this.getAudioLinkForLine(line);
        if (url) {
          links.push(url);
        }
      }
      return links;
    },
    async getAudioLinkForLine(line) {
      if (!('content' in line) || !line.content) {
        return null;
      }

      if (!('line_type' in line) || !line.line_type) {
        return null;
      }

      if (
        ![
          'html',
          'audio',
          'congregation',
          'leader',
          'leader_dialogue',
          'congregation_dialogue',
          'reader',
        ].includes(line.line_type)
      ) {
        return null;
      }

      const data = await this.$http.post(
        `${import.meta.env.VITE_API_URL}api/v1/audio`,
        {
          content: line.content,
          line_type: line.line_type,
        },
        {
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );
      try {
        return data.data.path;
      } catch {
        return null;
      }
    },
    async extraCollects() {
      if (this.serviceType !== 'office') {
        return '';
      }
      const full_office_name = this.office
        .replace('_', ' ')
        .toLowerCase()
        .split(' ')
        .map((s) => s.charAt(0).toUpperCase() + s.substring(1))
        .join(' ');
      const extraCollects =
        JSON.parse(await DynamicStorage.getItem('extraCollects')) || '';
      if (!extraCollects) {
        return '';
      }
      return Object.prototype.hasOwnProperty.call(
        extraCollects,
        full_office_name
      )
        ? extraCollects[full_office_name].join(',')
        : [];
    },
  },
};
</script>

<style scoped>
.office-header {
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
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

.display-settings-drawer__loading {
  font-size: 0.85rem;
  color: var(--el-text-color-secondary);
  margin-top: 0.5rem;
}

.display-settings-drawer__done {
  width: 100%;
  margin-top: 1rem;
}

:deep(.display-settings-drawer .sub-menu-item),
:deep(.display-settings-drawer .sub-menu-item .text-xs) {
  color: var(--el-text-color-primary);
  font-weight: 500;
}

:deep(.dark) .display-settings-drawer__content {
  color: var(--el-text-color-primary);
}

:deep(.dark) .display-settings-drawer .sub-menu-item,
:deep(.dark) .display-settings-drawer .sub-menu-item .text-xs {
  color: var(--el-text-color-primary);
}

:deep(.display-settings-drawer .el-drawer__body) {
  color: var(--el-text-color-primary);
}

:deep(.display-settings-drawer .font-size-block) {
  background-color: var(--el-fill-color) !important;
  border-color: var(--el-border-color-light) !important;
  box-shadow: none;
}

:deep(.display-settings-drawer .font-size-block .text-gray-400),
:deep(.display-settings-drawer .font-size-block .text-gray-500) {
  color: var(--el-text-color-secondary) !important;
}

:deep(.display-settings-drawer .font-size-block .text-gray-600),
:deep(.display-settings-drawer .font-size-block .text-gray-300) {
  color: var(--el-text-color-primary) !important;
}

:deep(.display-settings-drawer .el-slider__button) {
  border-color: var(--accent-color);
}

:deep(.display-settings-drawer .el-slider__bar) {
  background-color: var(--accent-color);
}

/* Ensure main content is centered and readable on large screens */
#main {
  max-width: 65ch;
  margin: 0 auto;
  padding: 0 1rem;
}
</style>
