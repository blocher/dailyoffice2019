<template>
  <div id="notch" class="notch"></div>
  <div class="m-4">
    <ThemeSwitcher />
  </div>
  <!--  <TopMenu v-if="!loading"/>-->
  <div
    class="w-full mt-10 mx-auto content-center flex items-center justify-center gap-2"
  >
    <h2>The Daily Office</h2>
  </div>
  <div
    class="w-full mt-4 mx-auto content-center flex items-center justify-center gap-2"
  >
    <a href="/">
      <el-button :type="isPray" round>Pray</el-button>
    </a>
    <a href="/settings">
      <el-button :type="isSettings" round>Settings</el-button>
    </a>
    <a href="/calendar">
      <el-button :type="isCalendar" round>Calendar</el-button>
    </a>
  </div>
  <div
    class="w-full mt-4 mx-auto content-center flex items-center justify-center gap-2"
  >
    <el-button v-if="showLinks" :type="isOther">
      <el-dropdown :hide-on-click="true" trigger="click">
        <span class="el-dropdown-link">
          More Resources
          <el-icon class="el-icon--right">
            <arrow-down />
          </el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <a href="/about">
              <el-dropdown-item>About</el-dropdown-item>
            </a>
            <el-dropdown-item disabled>--Prayer Resources--</el-dropdown-item>
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
            <el-dropdown-item disabled>--More--</el-dropdown-item>
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
    </el-button>
  </div>
  <div class="main-body">
    <Loading v-if="loading" />
    <!--    <BetaNote/>-->
    <el-alert v-if="error" :title="error" type="error" />
    <router-view v-if="!loading" :key="$route.fullPath" />
    <AdditionalLinks v-if="showLinks" ref="additionalLinks" />

    <AHPLogo />
    <p>
      <small><a href="/privacy-policy">Privacy Policy</a></small>
    </p>
  </div>

  <el-backtop :bottom="backtopBottom" />
</template>

<script>
import Loading from '@/components/Loading.vue';
import AHPLogo from '@/components/AHPLogo.vue';
import { event } from 'vue-gtag';
import { useActiveMeta, useMeta } from 'vue-meta';
import AdditionalLinks from '@/components/AdditionalLinks.vue';
import { ArrowDown } from '@element-plus/icons-vue';
import ThemeSwitcher from '@/components/ThemeSwitcher.vue';
import { DynamicStorage } from '@/helpers/storage.js';

export default {
  components: {
    AHPLogo,
    Loading,
    AdditionalLinks,
    ArrowDown,
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
    };
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
    backtopBottom() {
      return 80;
      //return this.audioEnabled ? 80 : 40;
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
</style>
