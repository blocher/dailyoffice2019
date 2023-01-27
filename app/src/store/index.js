import { createStore } from "vuex";
import { ElMessage } from "element-plus";
import { DynamicStorage } from "@/helpers/storage";
import router from "@/router";
import { getMessageOffset } from "@/helpers/getMessageOffest";

export default createStore({
  state: { settings: false, availableSettings: false },
  mutations: {
    saveAvailableSettings: (state, availableSettings) => {
      state.availableSettings = availableSettings;
    },
    saveSettings: async (state, settings) => {
      await DynamicStorage.setItem("settings", JSON.stringify(settings));
      state.settings = settings;
    },
  },
  actions: {
    async initializeSettings({ state, commit }) {
      const initializeAdditionalCollects = async () => {
        let isSetting = false;
        const offices = {
          morning_prayer_collects: "Morning Prayer",
          midday_prayer_collects: "Midday Prayer",
          evening_prayer_collects: "Evening Prayer",
          compline_collects: "Compline",
        };
        const result = {};
        for (const [key, value] of Object.entries(offices)) {
          if (router.currentRoute._value.query[key]) {
            result[value] = router.currentRoute._value.query[key].split(",");
            isSetting = true;
          }
        }
        if (isSetting) {
          await DynamicStorage.setItem("extraCollects", JSON.stringify(result));
        }
      };
      let availableSettings = state.availableSettings;
      const settings_store = await DynamicStorage.getItem("settings");
      const settings = settings_store
        ? JSON.parse(await DynamicStorage.getItem("settings"))
        : {};
      let applied = false;
      availableSettings.forEach((availableSetting) => {
        const key = availableSetting["name"];
        const value = availableSetting["options"][0]["value"];
        if (router.currentRoute._value.query[key]) {
          applied = true;
          settings[key] = router.currentRoute._value.query[key];
        } else if (settings[key] === undefined) {
          settings[key] = value;
        }
      });
      await DynamicStorage.setItem("settings", JSON.stringify(settings));
      state.settings = settings;
      await initializeAdditionalCollects();
      router.push({ path: router.currentRoute._value.fullPath, query: {} });
      if (applied) {
        ElMessage.success({
          title: "Saved",
          message:
            "New settings have been applied from the share link.<br><small><a href='/settings'>Review your settings.</a></small>",
          showClose: true,
          duration: 0,
          dangerouslyUseHTMLString: true,
          offset: getMessageOffset(),
        });
      }
      commit("saveSettings", settings);
      return state;
    },
  },
  modules: {},
});
