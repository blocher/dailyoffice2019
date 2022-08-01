import {createStore} from "vuex";
import {ElMessage} from "element-plus";

export default createStore({
    state: {settings: false, availableSettings: false},
    mutations: {
        saveAvailableSettings: (state, availableSettings) => {
            console.log("saving available");
            state.availableSettings = availableSettings;
        },
        saveSettings: (state, settings) => {
            localStorage.setItem("settings", JSON.stringify(settings));
            state.settings = settings;
        },
        initializeSettings: (state, app) => {
            const availableSettings = state.availableSettings;
            const settings_store = localStorage.getItem("settings");
            const settings = settings_store
                ? JSON.parse(localStorage.getItem("settings"))
                : {};
            let applied = false;
            availableSettings.forEach((availableSetting) => {
                const key = availableSetting["name"];
                const value = availableSetting["options"][0]["value"];
                console.log(key, value)
                if (app.$route.query[key]) {
                    applied = true;
                    settings[key] = app.$route.query[key];
                } else if (settings[key] === undefined) {
                    settings[key] = value;
                }
            });
            console.log(settings)
            localStorage.setItem("settings", JSON.stringify(settings));
            state.settings = settings;
            app.$router.replace({query: null});
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
