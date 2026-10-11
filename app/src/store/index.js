import { createStore } from 'vuex';
import { ElMessage } from 'element-plus';
import { DynamicStorage } from '@/helpers/storage';
import router from '@/router';
import { getMessageOffset } from '@/helpers/getMessageOffest';
import { decodeSettingsString } from '@/helpers/decodeSettingsString';

export default createStore({
  state: { settings: false, availableSettings: false },
  mutations: {
    saveAvailableSettings: (state, availableSettings) => {
      state.availableSettings = availableSettings;
    },
    saveSettings: (state, settings) => {
      state.settings = settings;
    },
  },
  actions: {
    async saveSettings({ commit }, settings) {
      commit('saveSettings', settings);
      await DynamicStorage.setItem('settings', JSON.stringify(settings));
    },
    async initializeSettings({ state, commit }) {
      const initializeAdditionalCollects = async () => {
        let isSetting = false;
        const offices = {
          morning_prayer_collects: 'Morning Prayer',
          midday_prayer_collects: 'Midday Prayer',
          evening_prayer_collects: 'Evening Prayer',
          compline_collects: 'Compline',
        };
        const result = {};
        for (const [key, value] of Object.entries(offices)) {
          if (router.currentRoute._value.query[key]) {
            result[value] = router.currentRoute._value.query[key].split(',');
            isSetting = true;
          }
        }
        if (isSetting) {
          await DynamicStorage.setItem('extraCollects', JSON.stringify(result));
        }
      };
      const availableSettings = state.availableSettings;
      const settings_store = await DynamicStorage.getItem('settings');
      const settings = settings_store
        ? JSON.parse(await DynamicStorage.getItem('settings'))
        : {};
      const setting_abbreviations = [];
      let applied = false;
      if (availableSettings) {
        availableSettings.forEach((availableSetting) => {
          const key = availableSetting['name'];
          const value = availableSetting['options'][0]['value'];
          const setting_string_order = availableSetting['setting_string_order'];
          const options = availableSetting['options'];
          if (router.currentRoute._value.query[key]) {
            applied = true;
            settings[key] = router.currentRoute._value.query[key];
          } else if (settings[key] === undefined) {
            settings[key] = value;
          }
          setting_abbreviations[setting_string_order] =
            setting_abbreviations[setting_string_order] || {};
          setting_abbreviations[setting_string_order].setting_name = key;
          setting_abbreviations[setting_string_order].options = [];
          options.forEach((settingOption) => {
            setting_abbreviations[setting_string_order].options.push({
              option_value: settingOption.value,
              abbreviation: settingOption.abbreviation,
            });
          });
        });
      }
      // If there is a settings URL parameter, then make this take precedence
      if (router.currentRoute._value.query['settings']) {
        let results = decodeSettingsString(
          router.currentRoute._value.query['settings'],
          setting_abbreviations
        );
        if (results.length === 0) {
          ElMessage.warning({
            title: 'Warning',
            message: 'The settings link is invalid',
            showClose: true,
            duration: 0,
            dangerouslyUseHTMLString: true,
            offset: getMessageOffset(),
          });
        }
        results.forEach(function (value) {
          applied = true;
          settings[value.settingName] = value.value;
        });
      }
      await DynamicStorage.setItem('settings', JSON.stringify(settings));
      await DynamicStorage.setItem(
        'settingAbbreviations',
        JSON.stringify(setting_abbreviations)
      );

      state.settings = settings;
      state.settingAbbreviations = setting_abbreviations;
      await initializeAdditionalCollects();
      router.push({ path: router.currentRoute._value.fullPath, query: {} });
      if (applied) {
        ElMessage.success({
          title: 'Saved',
          message:
            "New settings have been applied from the share link.<br><small><a href='/settings'>Review your settings.</a></small>",
          showClose: true,
          duration: 0,
          dangerouslyUseHTMLString: true,
          offset: getMessageOffset(),
        });
      }
      commit('saveSettings', settings);
      return state;
    },
  },
  modules: {},
});
