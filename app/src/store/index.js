import { createStore } from "vuex";
import { ElMessage } from "element-plus";

export default createStore({
  state: { settings: false, availableSettings: false },
  mutations: {
    saveAvailableSettings: (state, availableSettings) => {
      state.availableSettings = availableSettings;
    },
    saveSettings: (state, settings) => {
      localStorage.setItem("settings", JSON.stringify(settings));
      state.settings = settings;
    },
    initializeSettings: (state, app) => {
      const initializeAdditionalCollects = (app) => {
        let isSetting = false;
        const offices = {
          morning_prayer_collects: "Morning Prayer",
          midday_prayer_collects: "Midday Prayer",
          evening_prayer_collects: "Evening Prayer",
          compline_collects: "Compline",
        };
        const result = {};
        for (const [key, value] of Object.entries(offices)) {
          if (app.$route.query[key]) {
            result[value] = app.$route.query[key].split(",");
            isSetting = true;
          }
        }
        if (isSetting) {
          localStorage.setItem("extraCollects", JSON.stringify(result));
        }
      };
      const availableSettings = state.availableSettings;
      const settings_store = localStorage.getItem("settings");
      const settings = settings_store
        ? JSON.parse(localStorage.getItem("settings"))
        : {};
      let applied = false;
      availableSettings.forEach((availableSetting) => {
        const key = availableSetting["name"];
        const value = availableSetting["options"][0]["value"];
        if (app.$route.query[key]) {
          applied = true;
          settings[key] = app.$route.query[key];
        } else if (settings[key] === undefined) {
          settings[key] = value;
        }
      });
      localStorage.setItem("settings", JSON.stringify(settings));
      state.settings = settings;
      initializeAdditionalCollects(app);
      app.$router.replace({ query: null });
      if (applied) {
        ElMessage.success({
          title: "Saved",
          message:
            "New settings have been applied from the share link.<br><small><a href='/settings'>Review your settings.</a></small>",
          showClose: true,
          duration: 0,
          dangerouslyUseHTMLString: true,
        });
      }
    },
  },
  actions: {},
  modules: {},
});
