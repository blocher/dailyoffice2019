import { createStore } from "vuex";

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
    initializeSettings: (state) => {
      const availableSettings = state.availableSettings;
      const settings_store = localStorage.getItem("settings");
      const settings = settings_store
        ? JSON.parse(localStorage.getItem("settings"))
        : {};
      availableSettings.forEach((availableSetting) => {
        const key = availableSetting["name"];
        const value = availableSetting["options"][0]["value"];
        if (settings[key] === undefined) {
          settings[key] = value;
        }
      });
      localStorage.setItem("settings", JSON.stringify(settings));
      state.settings = settings;
      console.log("Initialized");
    },
  },
  actions: {},
  modules: {},
});
