import { Preferences } from '@capacitor/preferences';

export const DynamicStorage = {
  setItem: async (key, value) => {
    // console.log("SET ITEM", key, value, typeof value);
    if (typeof value === 'number') {
      value = value.toString();
    }
    await Preferences.set({
      key: key,
      value: value,
    });
    return value;
  },
  getItem: async (key) => {
    try {
      const { value } = await Preferences.get({ key: key });
      // console.log("GET ITEM", key, value);
      return value;
    } catch (error) {
      // console.log("ERROR", error);
      return '';
    }
  },
  deleteItem: async (key) => {
    await Preferences.remove({ key: key });
  },
};
