<template>
  <OfflineMode/>
  <TopMenu/>
  <div class="main">
    <Loading v-if="loading"/>
    <BetaNote/>
    <el-alert
        v-if="error" :title="error"
        type="error"
    />
    <router-view
        v-if="!loading" :key="$route.fullPath"
    />
    <AHPLogo/>
  </div>

  <el-backtop/>
</template>

<script>
import TopMenu from "@/components/TopMenu";
import Loading from "@/components/Loading";
import AHPLogo from "@/components/AHPLogo";
import {event} from 'vue-gtag'
import BetaNote from "@/components/BetaNote";
import {Workbox} from 'workbox-window';
import OfflineMode from "@/components/OfflineMode";

export default {
  components: {
    AHPLogo,
    TopMenu,
    Loading,
    BetaNote,
    OfflineMode,
  },
  data() {
    return {
      loading: true,
      open: false,
      isActive: true,
      name: this.$route.name,
      error: false,
    };
  },

  async created() {
    document.title = "The Daily Office";
    try {
      event('betaPageView')
      const settings_data = await this.$http.get(
          `${process.env.VUE_APP_API_URL}api/v1/available_settings/`
      );
      await this.$store.commit("saveAvailableSettings", settings_data.data);
      await this.$store.commit("initializeSettings", this);
      this.loading = false;
    } catch (e) {
      console.log(e);
      this.error =
          "There was an error loading the settings. Please try refreshing the page.";
      this.loading = false;
      return;
    }
    this.loading = false;
    this.manageOfflineWorker()
  },
  methods: {
    getPreLoadAPIEndpoints() {
      const settings = this.$store.state.settings;
      const queryString = Object.keys(settings)
          .map((key) => key + "=" + settings[key])
          .join("&");

      const base_routes = [
        "api/v1/office/morning_prayer/",
        "api/v1/office/midday_prayer/",
        "api/v1/office/evening_prayer/",
        "api/v1/office/compline/",
        "api/v1/family/morning_prayer",
        "api/v1/family/midday_prayer/",
        "api/v1/family/early_evening_prayer/",
        "api/v1/family/close_of_day_prayer/",
      ]

      const dates_to_cache = function () {
        const dates = [];
        const today = new Date();
        const year = today.getFullYear();
        const month = today.getMonth();
        const date = today.getDate();
        for (let i = -2; i < 31; i++) {
          const day = new Date(year, month, date + i);
          dates.push(day.toISOString().split("T")[0]);
        }
        return dates;
      };

      const office_routes = [];
      for (let day of dates_to_cache()) {
        for (let route of base_routes) {
          office_routes.push(`${route}${day}?${queryString}`);
        }
      }

      const calendar_routes = function () {
        const dates = [];
        const today = new Date();
        const year = today.getFullYear();
        const month = today.getMonth();
        const date = today.getDate();
        for (let i = -13; i < 13; i++) {
          const day = new Date(year, month + i, date)
          const parts = day.toISOString().split("-")
          const date_str = parts[0] + "-" + parts[1]
          dates.push(`/api/v1/calendar/${date_str}`);
        }
        return dates;
      }

      const psalm_routes = function () {
        const routes = ['/api/v1/psalms/', '/api/v1/psalms/topics/']
        for (let i = 1; i < 151; i++) {
          routes.push(`/api/v1/psalms/${i}`);
        }
        return routes;
      }

      const urls = [
        'api/v1/available_settings/',
        '/api/v1/about',
        '/api/v1/collect_categories/',
        '/collects',
        '/api/v1/collects',
      ].concat(office_routes).concat(calendar_routes()).concat(psalm_routes());
      return urls;
    },
    manageOfflineWorker() {
      let wb = null;
      try {
        wb = new Workbox('/service-worker.js');
      } catch (e) {
        console.log(e);
        return
      }
      wb.addEventListener('install', e => {
        // wb.skipWaiting();
      });

      const urls = this.getPreLoadAPIEndpoints();


      wb.addEventListener('activate', event => {

      });
      // Register the service worker after event listeners have been added.
      wb.register();
    },
  },
};
</script>
<style src="./assets/tailwind.css"></style>

<style lang="scss">

* {
  font-family: "Adobe Caslon Pro", serif;
  font-display: swap;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

[type='text']:focus, [type='email']:focus, [type='url']:focus, [type='password']:focus, [type='number']:focus, [type='date']:focus, [type='datetime-local']:focus, [type='month']:focus, [type='search']:focus, [type='tel']:focus, [type='time']:focus, [type='week']:focus, [multiple]:focus, textarea:focus, select:focus {
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

  .el-input__inner, el-select-dropdown__item {
    font-size: 16px;
  }

  .el-input__inner:active {
    border: none !important;
  }

  .main {
    // max-width: 620px;
    max-width: 1800px;
    display: block;
    text-align: left;
    padding: 1.4em;
    margin: 0 auto;
    clear: both;
    overflow-y: scroll;
  }

  .small-container {
    max-width: 700px;
    display: block;
    text-align: left;
    padding: 1.4em;
    margin: 0 auto;
    clear: both;
    overflow: visible;
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
    font-family: "Adobe Caslon Pro", serif;
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
  background-color: var(--el-input-bg-color, var(--el-fill-color-blank)) !important;
}

</style>
