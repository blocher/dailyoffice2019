import { Preferences } from '@capacitor/preferences';

// Browsers can deny storage outright (blocked site data, some embedded
// views), which makes every Preferences call throw a SecurityError. Values
// are kept here too so the app still works for the rest of the page load.
const memory = new Map();

export const DynamicStorage = {
  setItem: async (key, value) => {
    // console.log("SET ITEM", key, value, typeof value);
    if (typeof value === 'number') {
      value = value.toString();
    }
    memory.set(key, value);
    try {
      await Preferences.set({
        key: key,
        value: value,
      });
    } catch {
      // Storage unavailable: the in-memory copy stands in.
    }
    return value;
  },
  getItem: async (key) => {
    try {
      const { value } = await Preferences.get({ key: key });
      // console.log("GET ITEM", key, value);
      return value ?? memory.get(key) ?? value;
    } catch {
      // console.log("ERROR", error);
      return memory.get(key) ?? '';
    }
  },
  deleteItem: async (key) => {
    memory.delete(key);
    try {
      await Preferences.remove({ key: key });
    } catch {
      // Storage unavailable: nothing persisted to remove.
    }
  },
};
