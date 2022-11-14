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
          :tab-position="tabPosition" class="h-full"
      >
        <el-tab-pane label="Daily Office">
          <SettingsPanel
              :available-settings="availableSettings"
              site="Daily Office"
              name="Daily Office Settings"
          />
        </el-tab-pane>
        <el-tab-pane label="Family Prayer">
          <SettingsPanel
              :available-settings="availableSettings"
              site="Family Prayer"
              name="Family Prayer Settings"
          />
        </el-tab-pane>
      </el-tabs>
    </main>
  </div>
  <el-drawer
      v-model="drawerOpen" modal-class="pointer-events-none" direction="btt" :close-on-click-modal=false
      :lock-scroll=false
      :close-on-press-escape=false :show-close=false :with-header="false" size="auto" :modal=false :z-index=100>
    <h4>BENTITLE</h4>
    <p>Content</p>
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
    this.loading = false;
  },
  unmounted() {
    window.removeEventListener("resize", () => {
      this.windowWidth = window.innerWidth;
    });
  },
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
</style>
