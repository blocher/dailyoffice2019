<template>
  <div id="notch" class="notch"></div>
  
  <!-- Redesigned Header Section -->
  <header class="book-header" :class="seasonalAccentClass">
    <div class="header-container">
      <!-- Theme switcher moved to top right corner -->
      <div class="theme-switcher-container">
        <ThemeSwitcher />
      </div>
      
      <!-- Main title with elegant typography -->
      <div class="main-title-section">
        <h1 class="book-title">The Daily Office</h1>
        <div class="title-ornament">✠</div>
        <p class="book-subtitle">Book of Common Prayer 2019</p>
        <div v-if="seasonalColor" class="seasonal-indicator" :class="`seasonal-${seasonalColor}`"></div>
      </div>
      
      <!-- Primary navigation with refined styling -->
      <nav class="primary-navigation">
        <div class="nav-row primary-actions">
          <a href="/" class="nav-link" :class="{ active: isPray }">
            <span class="nav-text">Pray</span>
          </a>
          <a href="/settings" class="nav-link" :class="{ active: isSettings }">
            <span class="nav-text">Settings</span>
          </a>
          <a href="/calendar" class="nav-link" :class="{ active: isCalendar }">
            <span class="nav-text">Calendar</span>
          </a>
        </div>
        
        <!-- Secondary navigation dropdown with better styling -->
        <div class="nav-row secondary-actions" v-if="showLinks">
          <div class="resources-dropdown">
            <el-dropdown :hide-on-click="true" trigger="click" class="elegant-dropdown">
              <span class="dropdown-trigger">
                More Resources
                <span class="dropdown-arrow">▾</span>
              </span>
              <template #dropdown>
                <el-dropdown-menu class="elegant-dropdown-menu">
                  <a href="/about">
                    <el-dropdown-item>About</el-dropdown-item>
                  </a>
                  <el-dropdown-item disabled class="section-divider">Prayer Resources</el-dropdown-item>
                  <a href="/collects">
                    <el-dropdown-item>Collects</el-dropdown-item>
                  </a>
                  <a href="/psalms">
                    <el-dropdown-item>Psalms</el-dropdown-item>
                  </a>
                  <a href="/litany">
                    <el-dropdown-item>Great Litany</el-dropdown-item>
                  </a>
                  <a href="/readings">
                    <el-dropdown-item>Readings</el-dropdown-item>
                  </a>
                  <el-dropdown-item disabled class="section-divider">More</el-dropdown-item>
                  <el-dropdown-item
                    @click="
                      $refs.additionalLinks.$refs.shareSettings.toggleSharePanel()
                    "
                    >Share Settings
                  </el-dropdown-item>
                  <el-dropdown-item
                    @click="
                      $refs.additionalLinks.$refs.submitFeedback.showFeedbackPanel()
                    "
                    >Submit Feedback
                  </el-dropdown-item>
                  <el-dropdown-item
                    @click="$refs.additionalLinks.$refs.emailSignup.showEmailPanel()"
                    >Get Email Updates
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </nav>
    </div>
  </header>

  <div class="main-body">
    <Loading v-if="loading" />
    <el-alert v-if="error" :title="error" type="error" />
    <router-view v-if="!loading" :key="$route.fullPath" />
    <AdditionalLinks v-if="showLinks" ref="additionalLinks" />

    <AHPLogo />
    <p>
      <small><a href="/privacy-policy">Privacy Policy</a></small>
    </p>
  </div>

  <el-backtop :bottom="backtopBotton" />
</template>

<script>
import Loading from '@/components/Loading.vue';
import AHPLogo from '@/components/AHPLogo.vue';
import { event } from 'vue-gtag';
import { useActiveMeta, useMeta } from 'vue-meta';
import AdditionalLinks from '@/components/AdditionalLinks.vue';
import ThemeSwitcher from '@/components/ThemeSwitcher.vue';
import { DynamicStorage } from '@/helpers/storage.js';

export default {
  components: {
    AHPLogo,
    Loading,
    AdditionalLinks,
    ThemeSwitcher,
  },
  setup() {
    useMeta({
      htmlAttrs: { lang: 'en' },
      viewport: 'width=device-width, initial-scale=1.0, viewport-fit=cover',
    });
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
      seasonalColor: null,
    };
  },

  computed: {
    isPray() {
      return this.$route.name === 'Pray' || this.$route.name === 'Home';
    },
    isSettings() {
      return this.$route.name === 'Settings';
    },
    isCalendar() {
      return this.$route.name === 'calendar';
    },
    isOther() {
      return this.$route.name === 'About' ||
        this.$route.name === 'Collects' ||
        this.$route.name === 'readings' ||
        this.$route.name === 'litany' ||
        this.$route.name === 'Psalms';
    },
    backtopBotton() {
      return this.audioEnabled ? 80 : 40;
    },
    seasonalAccentClass() {
      return this.seasonalColor ? `seasonal-accent-${this.seasonalColor}` : '';
    },
  },
  async mounted() {
    const audioEnabled =
      (await DynamicStorage.getItem('audioEnabled', 'false')) === 'true'
        ? true
        : false;
    this.audioEnabled = audioEnabled;
  },
  async created() {
    document.title = 'The Daily Office';
    try {
      event('betaPageView');
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
    
    // Fetch seasonal color
    await this.fetchSeasonalColor();
  },
  methods: {
    async fetchSeasonalColor() {
      try {
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const day = String(today.getDate()).padStart(2, '0');
        const dateString = `${year}-${month}-${day}`;
        
        const response = await this.$http.get(
          `${import.meta.env.VITE_API_URL}api/v1/calendar/${dateString}/`
        );
        
        if (response.data && response.data.season && response.data.season.colors) {
          this.seasonalColor = response.data.season.colors[0];
        }
      } catch (error) {
        console.warn('Could not fetch seasonal color:', error);
        // Gracefully degrade - no seasonal accent
      }
    },
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
  --color-bg: #fff;
  --font-color: #333;
  --link-color: rgb(88, 166, 255);
  --font-on-white-background: #333;
  --el-text-color-primary: #333;
  --el-menu-bg-color: #fff;
  --el-color-white: rgb(28, 28, 33);
  --el-text-color-regular: #333;
  --el-calendar-selected-bg-color: #fff;
  --el-card-bg-color: white;
  --el-drawer-bg-color: white !important;
  --el-font-size-base: 16px;
  --el-collapse-header-height: auto !important;
  --sat: env(safe-area-inset-top);
  --sar: env(safe-area-inset-right);
  --sab: env(safe-area-inset-bottom);
  --sal: env(safe-area-inset-left);

  .el-calendar {
    --el-calendar-border: 1px solid black !important;
  }
}

:root.dark {
  --color-bg: rgb(28, 28, 33);
  --font-color: rgb(191, 191, 191);
  --link-color: rgb(88, 166, 255);
  --font-on-white-background: #333;

  --el-text-color-primary: rgb(191, 191, 191);
  --el-fill-color-blank: rgb(28, 28, 33);
  --el-color-white: rgb(28, 28, 33);
  --el-text-color-regular: rgb(191, 191, 191);
  --el-calendar-selected-bg-color: rgb(28, 28, 33);

  --el-card-bg-color: rgb(28, 28, 33);

  .el-calendar {
    --el-calendar-border: 1px solid grey !important;
  }
}

body {
  color: var(--font-color);
  background-color: var(--color-bg);
  margin-top: calc(env(safe-area-inset-top) + 1.4rem) !important;

  #notch {
    display: block;
    position: fixed;
    height: env(safe-area-inset-top);
    width: 100%;
    margin: 0;
    top: 0;
    left: 0;
    z-index: 9999;
    background-color: #26282a;
  }

  .el-input__inner,
  el-select-dropdown__item {
    font-size: 16px;
  }

  .el-input__inner:active {
    border: none !important;
  }

  .main-body {
    display: block;
    text-align: left;
    padding: 2.2em;
    margin: 0 auto;
    clear: both;
    overflow-y: scroll;
  }

  .small-container {
    max-width: 700px;
    display: block;
    text-align: left;
    padding: 2rem 0;
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

  a:link,
  a:visited,
  a:link.link,
  a:visited.link {
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
    color: #2c3e50;

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

/* Book-like Header Styles */
.book-header {
  background-color: var(--color-bg);
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  padding: 2rem 0 1.5rem 0;
  margin-bottom: 2rem;
}

:root.dark .book-header {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.header-container {
  max-width: 65ch;
  margin: 0 auto;
  padding: 0 2rem;
  position: relative;
}

.theme-switcher-container {
  position: absolute;
  top: 0;
  right: 2rem;
  z-index: 10;
}

.main-title-section {
  text-align: center;
  margin-bottom: 2rem;
}

.book-title {
  font-family: 'Adobe Caslon Pro', serif;
  font-size: 2.5rem;
  font-weight: 600;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  margin: 0 0 0.5rem 0;
  color: var(--font-color);
  line-height: 1.2;
}

.title-ornament {
  font-size: 1.5rem;
  margin: 0.5rem 0;
  color: var(--font-color);
  opacity: 0.7;
}

.book-subtitle {
  font-family: 'Adobe Caslon Pro', serif;
  font-size: 0.9rem;
  font-weight: 400;
  font-style: italic;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  margin: 0;
  color: var(--font-color);
  opacity: 0.8;
}

.primary-navigation {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.nav-row {
  display: flex;
  align-items: center;
  gap: 2rem;
}

.primary-actions {
  justify-content: center;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  padding-bottom: 1rem;
}

:root.dark .primary-actions {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.nav-link {
  text-decoration: none;
  color: var(--font-color);
  font-family: 'Adobe Caslon Pro', serif;
  font-size: 1rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.nav-link:hover {
  background-color: rgba(0, 0, 0, 0.05);
  border-color: rgba(0, 0, 0, 0.1);
}

:root.dark .nav-link:hover {
  background-color: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
}

.nav-link.active {
  background-color: rgba(0, 0, 0, 0.1);
  border-color: rgba(0, 0, 0, 0.2);
  font-weight: 700;
}

:root.dark .nav-link.active {
  background-color: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.3);
}

.secondary-actions {
  margin-top: 0.5rem;
}

.resources-dropdown {
  position: relative;
}

.dropdown-trigger {
  font-family: 'Adobe Caslon Pro', serif;
  font-size: 0.9rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--font-color);
  cursor: pointer;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.dropdown-trigger:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

:root.dark .dropdown-trigger:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.dropdown-arrow {
  font-size: 0.8rem;
  transition: transform 0.2s ease;
}

.section-divider {
  font-size: 0.8rem !important;
  font-weight: 600 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.1em !important;
  color: var(--font-color) !important;
  opacity: 0.6 !important;
  padding: 0.5rem 1rem !important;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1) !important;
  margin: 0.25rem 0 !important;
}

:root.dark .section-divider {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
}

/* Responsive Design */
@media (max-width: 768px) {
  .book-title {
    font-size: 2rem;
  }
  
  .header-container {
    padding: 0 1rem;
  }
  
  .theme-switcher-container {
    right: 1rem;
  }
  
  .nav-row {
    gap: 1rem;
  }
  
  .nav-link {
    font-size: 0.9rem;
    padding: 0.4rem 0.8rem;
  }
}

@media (max-width: 480px) {
  .book-title {
    font-size: 1.5rem;
  }
  
  .nav-row {
    flex-wrap: wrap;
    justify-content: center;
    gap: 0.5rem;
  }
  
  .nav-link {
    font-size: 0.8rem;
    padding: 0.3rem 0.6rem;
  }
}

/* Seasonal Color Integration */
.seasonal-indicator {
  width: 60px;
  height: 3px;
  margin: 0.5rem auto 0 auto;
  border-radius: 2px;
  opacity: 0.8;
  transition: all 0.3s ease;
}

.seasonal-red {
  background-color: #c21c13;
}

.seasonal-green {
  background-color: #077339;
}

.seasonal-white {
  background-color: #666;
  border: 1px solid rgba(0, 0, 0, 0.2);
}

:root.dark .seasonal-white {
  background-color: #ccc;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.seasonal-purple {
  background-color: #64147d;
}

.seasonal-black {
  background-color: #333;
}

.seasonal-rose {
  background-color: #ffb6c1;
}

/* Seasonal accent borders for header */
.book-header.seasonal-accent-red {
  border-bottom: 2px solid #c21c13;
}

.book-header.seasonal-accent-green {
  border-bottom: 2px solid #077339;
}

.book-header.seasonal-accent-white {
  border-bottom: 2px solid #666;
}

:root.dark .book-header.seasonal-accent-white {
  border-bottom: 2px solid #ccc;
}

.book-header.seasonal-accent-purple {
  border-bottom: 2px solid #64147d;
}

.book-header.seasonal-accent-black {
  border-bottom: 2px solid #333;
}

.book-header.seasonal-accent-rose {
  border-bottom: 2px solid #ffb6c1;
}

/* Seasonal accent for navigation active states */
.seasonal-accent-red .nav-link.active {
  border-color: #c21c13;
  background-color: rgba(194, 28, 19, 0.1);
}

.seasonal-accent-green .nav-link.active {
  border-color: #077339;
  background-color: rgba(7, 115, 57, 0.1);
}

.seasonal-accent-white .nav-link.active {
  border-color: #666;
  background-color: rgba(102, 102, 102, 0.1);
}

:root.dark .seasonal-accent-white .nav-link.active {
  border-color: #ccc;
  background-color: rgba(204, 204, 204, 0.1);
}

.seasonal-accent-purple .nav-link.active {
  border-color: #64147d;
  background-color: rgba(100, 20, 125, 0.1);
}

.seasonal-accent-black .nav-link.active {
  border-color: #333;
  background-color: rgba(51, 51, 51, 0.1);
}

.seasonal-accent-rose .nav-link.active {
  border-color: #ffb6c1;
  background-color: rgba(255, 182, 193, 0.1);
}
</style>
