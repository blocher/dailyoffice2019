import { createStore } from 'vuex';
import { toast } from '@/ui/feedback';
import { DynamicStorage } from '@/helpers/storage';
import router from '@/router';
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
          toast.warning({
            title: 'That settings link didn’t work',
            message: 'Your own settings are unchanged.',
            duration: 0,
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
      // Drop only the query parameters consumed above (a share link's
      // settings and extra collects) so other links, such as
      // /calendar?subscribe=1, keep theirs. Replace rather than push so the
      // cleanup doesn't add a history entry.
      const currentQuery = router.currentRoute._value.query || {};
      const settingNames = (availableSettings || []).map((s) => s.name);
      const consumed = Object.keys(currentQuery).filter(
        (key) =>
          key === 'settings' ||
          settingNames.includes(key) ||
          key.endsWith('_prayer_collects') ||
          key === 'compline_collects'
      );
      if (consumed.length) {
        const remaining = { ...currentQuery };
        consumed.forEach((key) => delete remaining[key]);
        await router.replace({
          path: router.currentRoute._value.path,
          query: remaining,
          hash: router.currentRoute._value.hash,
        });
      }
      if (applied) {
        toast.success({
          title: 'Settings applied from the share link',
          link: { to: '/settings', label: 'Review your settings' },
          duration: 0,
        });
      }
      commit('saveSettings', settings);
      return state;
    },
  },
  modules: {},
});
