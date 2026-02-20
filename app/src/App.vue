<template>
  <div id="notch" class="notch"></div>

  <!-- Header / Navigation -->
  <div
    class="fixed top-0 left-0 right-0 z-50 bg-white/95 dark:bg-gray-950/90 backdrop-blur border-b border-gray-200 dark:border-gray-800 px-4 pt-safe-top transition-transform duration-300"
    :class="{
      'translate-y-0': isHeaderVisible,
      '-translate-y-full': !isHeaderVisible,
    }"
  >
    <!-- Title Row -->
    <div class="flex items-center justify-between h-10">
      <span
        class="text-[11px] font-semibold text-gray-800 dark:text-gray-200 uppercase tracking-[0.14em]"
        >The Daily Office</span
      >
      <span
        class="hidden sm:inline text-[11px] text-gray-500 dark:text-gray-400 tracking-wide"
        >Book of Common Prayer, 2019 Edition</span
      >
    </div>

    <!-- Navigation Row -->
    <nav class="flex items-center justify-between pb-2 gap-2">
      <!-- Main Actions -->
      <div class="flex items-center gap-1.5">
        <router-link
          to="/"
          class="nav-chip"
          :class="isPray ? 'nav-chip--active' : 'nav-chip--inactive'"
        >
          Pray
        </router-link>

        <router-link
          to="/calendar"
          class="nav-chip"
          :class="isCalendar ? 'nav-chip--active' : 'nav-chip--inactive'"
        >
          Calendar
        </router-link>

        <router-link
          to="/settings"
          class="nav-chip"
          :class="isSettings ? 'nav-chip--active' : 'nav-chip--inactive'"
        >
          Settings
        </router-link>
      </div>

      <!-- More / Support -->
      <div class="flex items-center gap-1.5 pr-1">
        <button
          v-if="showLinks"
          @click.prevent="openDonation"
          class="nav-chip nav-chip--inactive"
        >
          <font-awesome-icon :icon="['fad', 'heart']" class="nav-chip__icon" />
          <span class="support-label">Support</span>
        </button>

        <el-dropdown
          v-if="showLinks"
          :hide-on-click="true"
          trigger="click"
          size="small"
          placement="bottom-end"
          popper-class="more-menu-popper"
          :popper-options="moreMenuPopperOptions"
        >
          <button class="nav-chip nav-chip--inactive">
            More
            <el-icon class="nav-chip__icon"><arrow-down /></el-icon>
          </button>
          <template #dropdown>
            <el-dropdown-menu>
              <a href="/about"><el-dropdown-item>About</el-dropdown-item></a>
              <el-dropdown-item divided disabled
                >--Resources--</el-dropdown-item
              >
              <a href="/collects"
                ><el-dropdown-item>Collects</el-dropdown-item></a
              >
              <a href="/psalms"><el-dropdown-item>Psalms</el-dropdown-item></a>
              <a href="/litany"
                ><el-dropdown-item>Great Litany</el-dropdown-item></a
              >
              <a href="/readings"
                ><el-dropdown-item>Readings</el-dropdown-item></a
              >

              <el-dropdown-item
                divided
                @click="
                  $refs.additionalLinks.$refs.shareSettings.toggleSharePanel()
                "
                >Share Settings</el-dropdown-item
              >
              <el-dropdown-item
                @click="
                  $refs.additionalLinks.$refs.submitFeedback.showFeedbackPanel()
                "
                >Submit Feedback</el-dropdown-item
              >
              <el-dropdown-item
                @click="
                  $refs.additionalLinks.$refs.emailSignup.showEmailPanel()
                "
                >Get Email Updates</el-dropdown-item
              >

              <el-dropdown-item divided disabled
                >--Contribute--</el-dropdown-item
              >
              <el-dropdown-item @click="openDonation"
                >Support Financially</el-dropdown-item
              >
              <a
                href="https://github.com/blocher/dailyoffice2019"
                target="_blank"
                rel="noopener noreferrer"
                ><el-dropdown-item>GitHub Code</el-dropdown-item></a
              >

              <template v-if="isWeb">
                <el-dropdown-item divided disabled>--Apps--</el-dropdown-item>
                <el-dropdown-item @click="openAppStore('ios')"
                  ><font-awesome-icon :icon="['fab', 'fa-apple']" /> iOS
                  App</el-dropdown-item
                >
                <el-dropdown-item @click="openAppStore('android')"
                  ><font-awesome-icon :icon="['fab', 'fa-android']" /> Android
                  App</el-dropdown-item
                >
              </template>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </nav>
  </div>

  <div class="main-body pt-24" :style="mainBodyStyle">
    <Loading v-if="loading" />
    <!--    <BetaNote/>-->
    <el-alert v-if="error" :title="error" type="error" />
    <router-view v-if="!loading" :key="$route.fullPath" />
    <footer
      v-if="showLinks"
      class="mt-12 border-t border-gray-200 dark:border-gray-800 bg-white/40 dark:bg-gray-900/20"
    >
      <div class="max-w-3xl mx-auto px-4 py-10 space-y-8">
        <AdditionalLinks ref="additionalLinks" />

        <div class="grid md:grid-cols-2 gap-4 items-stretch">
          <div class="h-full">
            <DonationPrompt variant="long" class="h-full" :compact="true" />
          </div>

          <div class="h-full">
            <AHPLogo />
          </div>
        </div>

        <div class="space-y-3 text-center">
          <p class="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
            2019 Book of Common Prayer used by permission of the Anglican Church
            in North America
          </p>
          <p class="text-xs text-gray-500 dark:text-gray-400">
            <a
              href="/privacy-policy"
              class="hover:text-gray-700 dark:hover:text-gray-200 transition-colors"
              >Privacy Policy</a
            >
          </p>
        </div>
      </div>
    </footer>
  </div>

  <el-backtop :bottom="backtopBottom" />
</template>

<script>
import Loading from '@/components/Loading.vue';
import AHPLogo from '@/components/AHPLogo.vue';
import { useActiveMeta, useMeta } from 'vue-meta';
import { useRoute } from 'vue-router';
import AdditionalLinks from '@/components/AdditionalLinks.vue';
import { ArrowDown } from '@element-plus/icons-vue';
import DonationPrompt from '@/components/DonationPrompt.vue';
import { DynamicStorage } from '@/helpers/storage.js';
import { Browser } from '@capacitor/browser';
import { Capacitor } from '@capacitor/core';

export default {
  components: {
    AHPLogo,
    Loading,
    AdditionalLinks,
    ArrowDown,
    DonationPrompt,
  },
  setup() {
    const route = useRoute();
    // Bind title to current route meta so it doesn't revert to the default
    useMeta(() => ({
      title: route.meta?.title || 'The Daily Office',
      htmlAttrs: { lang: 'en' },
      viewport: 'width=device-width, initial-scale=1.0, viewport-fit=cover',
    }));
    useActiveMeta();
  },
  data() {
    return {
      loading: true,
      open: false,
      isActive: true,
      name: this.$route.name,
      error: false,
      showLinks: false,
      audioEnabled: false,
      isWeb: false,
      moreMenuPopperOptions: {
        modifiers: [
          {
            name: 'offset',
            options: {
              offset: [-8, 10],
            },
          },
        ],
      },
      isHeaderVisible: true,
      lastScrollPosition: 0,
      isAudioPlayerVisible: false, // Track if player is actually showing
      audioBarHeight: 0,
      settingsBarHeight: 0,
    };
  },

  methods: {
    handleAudioVisibility(payload) {
      if (payload && typeof payload === 'object') {
        const isVisible = Boolean(payload.visible);
        const height = Number(payload.height) || 0;
        this.isAudioPlayerVisible = isVisible;
        this.audioBarHeight = isVisible ? height : 0;
        return;
      }
      const isVisible = Boolean(payload);
      this.isAudioPlayerVisible = isVisible;
      this.audioBarHeight = isVisible ? 132 : 0;
    },
    handleSettingsBarVisibility(payload) {
      if (payload && typeof payload === 'object') {
        const isVisible = Boolean(payload.visible);
        const height = Number(payload.height) || 0;
        this.settingsBarHeight = isVisible ? height : 0;
        return;
      }
      const isVisible = Boolean(payload);
      this.settingsBarHeight = isVisible ? 140 : 0;
    },
    onAudioVisibilityEvent(event) {
      this.handleAudioVisibility(event.detail);
    },
    onSettingsBarVisibilityEvent(event) {
      this.handleSettingsBarVisibility(event.detail);
    },
    handleScroll() {
      // Don't hide for negative scroll (bounce effect) or very top
      const currentScrollPosition =
        window.pageYOffset || document.documentElement.scrollTop;

      if (currentScrollPosition < 0) {
        return;
      }

      // Always show if near top
      if (currentScrollPosition < 60) {
        this.isHeaderVisible = true;
        this.lastScrollPosition = currentScrollPosition;
        return;
      }

      // Show if scrolling up, hide if scrolling down
      this.isHeaderVisible = currentScrollPosition < this.lastScrollPosition;
      this.lastScrollPosition = currentScrollPosition;
    },
    async openDonation() {
      await Browser.open({ url: 'https://ko-fi.com/dailyoffice' });
    },
    async openAppStore(platform) {
      const urls = {
        ios: 'https://apps.apple.com/us/app/the-daily-office/id1513851259',
        android:
          'https://play.google.com/store/apps/details?id=com.dailyoffice2019.app&hl=en_US',
      };
      await Browser.open({ url: urls[platform] });
    },
  },

  computed: {
    isPray() {
      return this.$route.name === 'Pray' || this.$route.name === 'Home'
        ? 'primary'
        : '';
    },
    isSettings() {
      return this.$route.name === 'Settings' ? 'primary' : '';
    },
    isCalendar() {
      return this.$route.name === 'calendar' ? 'primary' : '';
    },
    isOther() {
      return this.$route.name === 'About' ||
        this.$route.name === 'Collects' ||
        this.$route.name === 'readings' ||
        this.$route.name === 'litany' ||
        this.$route.name === 'Psalms'
        ? 'primary'
        : '';
    },
    bottomFixedOffset() {
      const tallestBar = Math.max(
        this.audioBarHeight,
        this.settingsBarHeight,
        0
      );
      return tallestBar > 0 ? tallestBar + 16 : 0;
    },
    mainBodyStyle() {
      return {
        paddingBottom: `calc(${this.bottomFixedOffset}px + env(safe-area-inset-bottom))`,
      };
    },
    backtopBottom() {
      return this.bottomFixedOffset > 0 ? this.bottomFixedOffset + 20 : 20;
    },
  },
  async mounted() {
    window.addEventListener('scroll', this.handleScroll);
    document.addEventListener(
      'audio-player-visibility',
      this.onAudioVisibilityEvent
    );
    document.addEventListener(
      'settings-bottom-bar-visibility',
      this.onSettingsBarVisibilityEvent
    );

    const audioEnabled =
      (await DynamicStorage.getItem('audioEnabled', 'false')) === 'true'
        ? true
        : false;
    this.audioEnabled = audioEnabled;

    // Check if we're on web platform
    const platform = Capacitor.getPlatform();
    this.isWeb = platform === 'web';
  },
  unmounted() {
    window.removeEventListener('scroll', this.handleScroll);
    document.removeEventListener(
      'audio-player-visibility',
      this.onAudioVisibilityEvent
    );
    document.removeEventListener(
      'settings-bottom-bar-visibility',
      this.onSettingsBarVisibilityEvent
    );
  },
  async created() {
    try {
      const settings_data = await this.$http.get(
        `${import.meta.env.VITE_API_URL}api/v1/available_settings/`
      );
      await this.$store.commit('saveAvailableSettings', settings_data.data);
      await this.$store.dispatch('initializeSettings');
      this.loading = false;
      await this.$nextTick();
      this.showLinks = true;
    } catch {
      this.error =
        'There was an error loading the settings. Please try refreshing the page.';
      this.loading = false;
      await this.$nextTick();
      this.showLinks = true;
      return;
    }
    this.loading = false;
    await this.$nextTick();
    this.showLinks = true;
  },
};
</script>
<style src="./assets/tailwind.css"></style>

<style lang="scss">
@forward 'element-plus/theme-chalk/src/common/var.scss' with (
  $collapse: (
    'header-height': auto,
  )
);

@font-face {
  font-family: 'Adobe Caslon Pro';
  src:
    url('/assets/fonts/ACaslonPro-Regular.woff2') format('woff2'),
    url('/assets/fonts/ACaslonPro-Regular.woff') format('woff'),
    url('/assets/fonts/ACaslonPro-Regular.ttf') format('truetype');
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}

@font-face {
  font-family: 'Adobe Caslon Pro';
  src:
    url('/assets/fonts/ACaslonPro-Italic.woff2') format('woff2'),
    url('/assets/fonts/ACaslonPro-Italic.woff') format('woff'),
    url('/assets/fonts/ACaslonPro-Italic.ttf') format('truetype');
  font-weight: 400;
  font-style: italic;
  font-display: swap;
}

@font-face {
  font-family: 'Adobe Caslon Pro';
  src:
    url('/assets/fonts/ACaslonPro-Semibold.woff2') format('woff2'),
    url('/assets/fonts/ACaslonPro-Semibold.woff') format('woff'),
    url('/assets/fonts/ACaslonPro-Semibold.ttf') format('truetype');
  font-weight: 600;
  font-style: normal;
  font-display: swap;
}

@font-face {
  font-family: 'Adobe Caslon Pro';
  src:
    url('/assets/fonts/ACaslonPro-SemiboldItalic.woff2') format('woff2'),
    url('/assets/fonts/ACaslonPro-SemiboldItalic.woff') format('woff'),
    url('/assets/fonts/ACaslonPro-SemiboldItalic.ttf') format('truetype');
  font-weight: 600;
  font-style: italic;
  font-display: swap;
}

@font-face {
  font-family: 'Adobe Caslon Pro';
  src:
    url('/assets/fonts/ACaslonPro-Bold.woff2') format('woff2'),
    url('/assets/fonts/ACaslonPro-Bold.woff') format('woff'),
    url('/assets/fonts/ACaslonPro-Bold.ttf') format('truetype');
  font-weight: 700;
  font-style: normal;
  font-display: swap;
}

@font-face {
  font-family: 'Adobe Caslon Pro';
  src:
    url('/assets/fonts/ACaslonPro-BoldItalic.woff2') format('woff2'),
    url('/assets/fonts/ACaslonPro-BoldItalic.woff') format('woff'),
    url('/assets/fonts/ACaslonPro-BoldItalic.ttf') format('truetype');
  font-weight: 700;
  font-style: italic;
  font-display: swap;
}

@font-face {
  font-family: 'Adobe Caslon Pro';
  src: url('/assets/fonts/') format('woff2');
  font-display: swap;
}

* {
  font-family: 'Adobe Caslon Pro', serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

[type='text']:focus,
[type='email']:focus,
[type='url']:focus,
[type='password']:focus,
[type='number']:focus,
[type='date']:focus,
[type='datetime-local']:focus,
[type='month']:focus,
[type='search']:focus,
[type='tel']:focus,
[type='time']:focus,
[type='week']:focus,
[multiple]:focus,
textarea:focus,
select:focus {
  border-color: transparent;
  outline: 0px !important;
  box-shadow: 0 0 0 0 transparent !important;
}

:root {
  --color-bg: #f8fafc;
  --font-color: #111827;
  --font-on-white-background: #111827;
  --header-bg-color: #ffffff;
  --accent-color: #4f46e5;
  --accent-contrast: #ffffff;
  --link-color: var(--accent-color);
  --el-color-primary: var(--accent-color);

  --el-text-color-primary: #111827;
  --el-text-color-secondary: #6b7280;
  --el-text-color-regular: #374151;
  --el-text-color-placeholder: #9ca3af;
  --el-fill-color-blank: #ffffff;
  --el-fill-color: #f3f4f6;
  --el-fill-color-light: #f9fafb;
  --el-border-color: #d1d5db;
  --el-border-color-light: #e5e7eb;
  --el-border-color-lighter: #f3f4f6;
  --el-bg-color: #ffffff;
  --el-bg-color-overlay: #ffffff;
  --el-bg-color-page: #f8fafc;
  --el-menu-bg-color: #ffffff;
  --el-color-white: #ffffff;
  --el-calendar-selected-bg-color: #eef2ff;
  --el-card-bg-color: #ffffff;
  --el-drawer-bg-color: #ffffff !important;
  --el-mask-color: rgba(15, 23, 42, 0.45);
  --el-overlay-color-lighter: rgba(15, 23, 42, 0.28);

  --season-red: #c21c13;
  --season-green: #077339;
  --season-purple: #64147d;
  --season-white: #d4af37;
  --season-black: #1a1a1a;
  --season-rose: #c2417f;
  --season-blue: #1d4ed8;

  --el-font-size-base: 16px;
  --el-collapse-header-height: auto !important;
  --sat: env(safe-area-inset-top);
  --sar: env(safe-area-inset-right);
  --sab: env(safe-area-inset-bottom);
  --sal: env(safe-area-inset-left);

  .el-calendar {
    --el-calendar-border: 1px solid #d1d5db !important;
  }
}

:root.dark {
  --color-bg: #111827;
  --font-color: #e5e7eb;
  --font-on-white-background: #e5e7eb;
  --header-bg-color: #111827;
  --accent-color: #93c5fd;
  --accent-contrast: #0b1220;
  --link-color: var(--accent-color);
  --el-color-primary: var(--accent-color);

  --el-text-color-primary: #f3f4f6;
  --el-text-color-secondary: #9ca3af;
  --el-text-color-placeholder: #6b7280;
  --el-fill-color-blank: #111827;
  --el-fill-color: #1f2937;
  --el-fill-color-light: #273244;
  --el-color-white: #1f2937;
  --el-text-color-regular: #d1d5db;
  --el-calendar-selected-bg-color: #1f2937;
  --el-border-color: #475569;
  --el-border-color-light: #334155;
  --el-border-color-lighter: #1e293b;
  --el-bg-color: #111827;
  --el-bg-color-overlay: #1f2937;
  --el-bg-color-page: #0b1220;
  --el-disabled-bg-color: #374151;
  --el-disabled-text-color: #9ca3af;
  --el-menu-bg-color: #111827;
  --el-card-bg-color: #111827;
  --el-drawer-bg-color: #111827 !important;
  --el-mask-color: rgba(0, 0, 0, 0.6);
  --el-overlay-color-lighter: rgba(0, 0, 0, 0.4);

  --season-red: #f87171;
  --season-green: #34d399;
  --season-purple: #c084fc;
  --season-white: #facc15;
  --season-black: #9ca3af;
  --season-rose: #f472b6;
  --season-blue: #60a5fa;

  .el-calendar {
    --el-calendar-border: 1px solid #475569 !important;
  }

  .el-button {
    --el-button-bg-color: #1f2937;
    --el-button-border-color: #334155;
    --el-button-text-color: #e5e7eb;
    --el-button-hover-bg-color: #273244;
    --el-button-hover-border-color: #475569;
    --el-button-hover-text-color: #ffffff;
  }

  .el-tabs__item {
    color: #9ca3af;

    &.is-active {
      color: #f3f4f6;
    }
  }

  .el-switch {
    --el-switch-off-color: #475569;
  }

  .el-tag {
    --el-tag-bg-color: #1f2937;
    --el-tag-border-color: #475569;
    --el-tag-text-color: #e5e7eb;
  }
}

.el-dropdown-menu,
.el-popper.is-pure {
  background-color: var(--el-bg-color-overlay);
  border: 1px solid var(--el-border-color-light);
}

.el-dropdown-menu__item,
.el-dropdown-menu__item.is-disabled {
  color: var(--el-text-color-regular);
}

.el-dropdown-menu__item:not(.is-disabled):hover,
.el-dropdown-menu__item:not(.is-disabled):focus {
  background-color: var(--el-fill-color-light);
  color: var(--accent-color);
}

.more-menu-popper {
  max-width: calc(100vw - 1rem);
}

.el-switch,
:root.dark .el-switch {
  --el-switch-on-color: var(--accent-color);
}

.el-button--primary,
:root.dark .el-button--primary {
  --el-button-bg-color: var(--accent-color);
  --el-button-border-color: var(--accent-color);
  --el-button-text-color: var(--accent-contrast);
  --el-button-hover-bg-color: var(--accent-color);
  --el-button-hover-border-color: var(--accent-color);
  --el-button-hover-text-color: var(--accent-contrast);
  --el-button-active-bg-color: var(--accent-color);
  --el-button-active-border-color: var(--accent-color);
  --el-button-active-text-color: var(--accent-contrast);
}

.el-button--primary:not(.is-disabled):hover {
  filter: brightness(0.95);
}

.nav-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: inherit;
  gap: 0.3rem;
  min-height: 2rem;
  width: 6.5rem;
  min-width: 6.5rem;
  padding: 0.375rem 0.875rem;
  border-width: 1px;
  border-style: solid;
  border-radius: 0.375rem;
  font-size: 0.72rem;
  font-weight: 600;
  line-height: 1;
  white-space: nowrap;
  transition:
    background-color 0.2s ease,
    border-color 0.2s ease,
    color 0.2s ease,
    filter 0.2s ease;
}

a.nav-chip,
button.nav-chip {
  font-size: 0.72rem;
}

.nav-chip--inactive {
  background-color: #ffffff;
  color: #374151;
  border-color: #d1d5db;
}

.nav-chip--inactive:hover {
  background-color: #f9fafb;
  color: #111827;
  border-color: #9ca3af;
}

:root.dark .nav-chip--inactive {
  background-color: #111827;
  color: #d1d5db;
  border-color: #374151;
}

:root.dark .nav-chip--inactive:hover {
  background-color: #1f2937;
  color: #f3f4f6;
  border-color: #4b5563;
}

.nav-chip--active {
  background-color: var(--accent-color);
  color: var(--accent-contrast);
  border-color: var(--accent-color);
}

.nav-chip--active:hover {
  filter: brightness(0.95);
}

.nav-chip__icon {
  color: var(--accent-color);
  font-size: 0.72rem;
}

@media (max-width: 640px) {
  .nav-chip {
    width: auto;
    min-width: auto;
    padding: 0.35rem 0.55rem;
  }

  .support-label {
    display: none;
  }
}

body {
  color: var(--font-color);
  background-color: var(--color-bg);
  margin-top: 0 !important;
  padding-top: env(safe-area-inset-top);

  #notch {
    display: block;
    position: fixed;
    height: env(safe-area-inset-top);
    width: 100%;
    margin: 0;
    top: 0;
    left: 0;
    z-index: 10000; // Ensure notch is above fixed header
    background-color: var(--header-bg-color);
  }

  .el-input__inner,
  el-select-dropdown__item {
    font-size: 16px;
  }

  .el-input__inner:active {
    border: none !important;
  }

  .main-body {
    // Override existing padding to account for fixed header
    padding-top: calc(5rem + env(safe-area-inset-top)) !important;
  }

  .small-container {
    max-width: 700px;
    display: block;
    text-align: left;
    padding: 2rem 1rem;
    margin: 0 auto;
    clear: both;
    overflow: visible;
  }

  #main {
    max-width: 65ch;
    margin: 0 auto 5rem;
  }

  h1,
  h2,
  h3,
  h4 {
    font-weight: 600;
    font-style: normal;
    letter-spacing: 0.1em;
    text-align: center;
    margin: 0.2em;
    padding-top: 2em;
  }

  h1,
  h2,
  h3 {
    text-transform: uppercase;
  }

  h1 {
    font-size: 1.3em;
    line-height: 1.5em;
  }

  h2 {
    font-size: 1em;

    &.intro-heading {
      font-size: 0.5em;
      margin: 1em 0 0 0;
      padding: 0;
      line-height: 0.6em;
      letter-spacing: 0.1em;
    }
  }

  h3 {
    padding-top: 30px;
    margin-bottom: 5px;
    font-size: 1em;
    line-height: 1.4em;

    &.intro-heading {
      font-size: 0.4em;
      margin: 0;
      padding: 0;
      line-height: 0.5em;
      letter-spacing: 0.1em;
    }
  }

  h4 {
    margin-top: 0;
    padding-top: 0;
    font-weight: 600;
    font-style: italic;
    font-size: 0.9em;
    line-height: 1em;
    margin-bottom: 1em;
  }

  h5 {
    font-weight: 300;
    text-align: right;
    font-size: 0.9em;
    margin: 10px 0;
    text-transform: uppercase;
  }

  p {
    font-family: 'Adobe Caslon Pro', serif;
    font-display: swap;
    font-weight: 300;
    font-style: normal;

    &.rubric {
      line-height: 0.9em;
      margin: 10px 0;
    }

    &.indent {
      margin: 0 0 0 1em;
    }

    &.hangingIndent {
      text-indent: -1em;
      margin-left: 1em;
    }

    strong {
      font-weight: 700;
    }
  }

  a:link:not(.nav-chip),
  a:visited:not(.nav-chip),
  a.link:link:not(.nav-chip),
  a.link:visited:not(.nav-chip) {
    color: var(--link-color);
  }

  #container {
    max-width: 580px;
    display: block;
    text-align: left;
    padding: 1.4em;
    margin: 0 auto 1em;
    clear: both;
  }
}

#nav {
  padding: 30px;

  a {
    font-weight: bold;
    color: var(--font-color, #2c3e50);

    &.router-link-exact-active {
      color: #42b983;
    }
  }
}

.el-input__inner {
  background-color: var(
    --el-input-bg-color,
    var(--el-fill-color-blank)
  ) !important;
}

.el-drawer {
  padding-top: env(safe-area-inset-top);
}

.pt-safe-top {
  padding-top: env(safe-area-inset-top);
}
</style>
