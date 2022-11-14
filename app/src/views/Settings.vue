<template>
  <div class="home">
    <h1>Settings</h1>
    <Loading v-if="loading"/>
    <main
        v-if="!loading"
        v-cloak
        class="max-w-6xl mx-auto pt-10 pb-12 px-4 lg:pb-16"
    >
      <el-tabs
          v-model="openTab" :tab-position="tabPosition" class="h-full"
      >
        <el-tab-pane label="Daily Office" name="office">
          <SettingsPanel
              :available-settings="availableSettings"
              site="Daily Office"
              name="Daily Office Settings"
              :advanced="advanced"
          />
        </el-tab-pane>
        <el-tab-pane label="Family Prayer" name="family">
          <SettingsPanel
              :available-settings="availableSettings"
              site="Family Prayer"
              name="Family Prayer Settings"
              :advanced="advanced"
          />
        </el-tab-pane>
      </el-tabs>
    </main>
  </div>
  <el-drawer
      v-model="drawerOpen" modal-class="pointer-events-none" direction="btt" :close-on-click-modal=false
      :lock-scroll=false
      :close-on-press-escape=false :show-close=false :with-header="false" size="auto" :modal=false :z-index=100
  >
    <h4>Displayed Settings</h4>
    <div class="w-full">

      <div class="wrapper w-full">
        <div class="text-right"><small>Daily Office</small></div>
        <div class="text-center">
          <el-switch
              v-model="openTab"
              class="ml-2"
              active-color="#e5e7eb"
              inactive-color="#e5e7eb"
              active-value="family"
              inactive-value="office"
              @change="toggleOffice"
          />
        </div>
        <div class="text-left"><small>Family Prayer</small></div>
        <div class="text-right"><small>Frequently Used</small></div>
        <div class="text-center">
          <el-switch
              v-model="advanced"
              class="ml-2"
              active-color="#e5e7eb"
              inactive-color="#e5e7eb"
              @change="toggleAdvanced"
          />
        </div>
        <div class="text-left"><small>All Settings</small></div>

      </div>
    </div>
  </el-drawer>
</template>

<script>
// @ is an alias to /src

import Loading from "@/components/Loading";
import SettingsPanel from "@/components/SettingsPanel";

export default {
  name: "Settings",
  components: {
    Loading,
    SettingsPanel,
  },
  data() {
    return {
      counter: 0,
      availableSettings: null,
      familyPrayerSettings: null,
      dailyOfficeSettings: null,
      loading: true,
      windowWidth: 0,
      drawerOpen: true,
      advanced: false,
      openTab: "office",
    };
  },
  computed: {
    // a computed getter
    tabPosition: function () {
      return "top"
      // return this.windowWidth > 780 ? "left" : "top";
    },
  },
  mounted() {
    this.loading = true;
    this.windowWidth = window.innerWidth;
    window.addEventListener("resize", () => {
      this.windowWidth = window.innerWidth;
    });
    this.availableSettings = this.$store.state.availableSettings;
    const settings = this.$store.state.settings;
    this.availableSettings.forEach((setting, i) => {
      const name = setting.name;
      this.availableSettings[i].active = settings[name];
    });
    this.dailyOfficeSettings = this.availableSettings.filter(
        (setting) => setting.site_name == "Daily Office"
    );
    this.familyPrayerSettings = this.availableSettings.filter(
        (setting) => setting.site_name == "Family Prayer"
    );
    if (localStorage.advancedSettings) {
      const stored = localStorage.advancedSettings;
      this.advanced = stored == "true" ? true : false;
    } else {
      localStorage.advancedSettings = false;
    }
    if (localStorage.settingsPane) {
      const stored = localStorage.settingsPane;
      if (stored) {
        this.openTab = stored;
      } else {
        localStorage.settingsPane = "office";
      }
    }
    this.loading = false;
  },

  unmounted() {
    window.removeEventListener("resize", () => {
      this.windowWidth = window.innerWidth;
    });
  },
  methods: {
    toggleAdvanced(value) {
      localStorage.advancedSettings = value;
    },
    toggleOffice(value) {
      this.openTab = value;
      localStorage.settingsPane = value;
    }
  }
};
</script>

<style>
[v-cloak] {
  display: none;
}

.pointer-events-none {
  pointer-events: none;
}

.el-drawer {
  pointer-events: auto;
}


.wrapper {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  grid-gap: 1rem;
}

</style>
