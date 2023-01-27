<template>
  <h3>Available offline until: {{ syncedUntil }}</h3>
</template>


<script>

import {getCurrentInstance} from 'vue';
import {createTablesNoEncryption} from '@/utils/utils-db-no-encryption';
import {precacheURL} from "@/utils/request";
import {Network} from "@capacitor/network";
import {getOfficeURL} from "@/utils/officeURL";

const alwaysSync = [
  'api/v1/available_settings/',
  'api/v1/about',
  'api/v1/collects',
  'api/v1/litany',
  'api/v1/collects',
  'api/v1/psalms/topics',
  'api/v1/psalms',
  'api/v1/grouped_collects',
]

const valid_daily_offices = [
  "morning_prayer",
  "midday_prayer",
  "evening_prayer",
  "compline",
];
const valid_family_offices = [
  "morning_prayer",
  "midday_prayer",
  "early_evening_prayer",
  "close_of_day_prayer",
];
export default {
  data() {
    return {
      content: 'starting',
      syncedUntil: false,
    };
  },
  created: async function () {
    // Running the test
    await this.setupDb();
    await this.sync();
  },
  methods: {
    async setupDb() {

      const app = getCurrentInstance()
      const sqlite = app?.appContext.config.globalProperties.$sqlite;

      const db = await sqlite.createConnection("offlineDB", false, "no-encryption", 1);

      let ret = await db.open();

      // create tables in db
      ret = await db.execute(createTablesNoEncryption);
      if (ret.changes.changes < 0) {
        return false;
      }

      app?.appContext.config.globalProperties.$existingConn.setExistConn(true);
      return true;
    },
    async syncAlwaysSyncLinks() {
      await alwaysSync.forEach(async (url) => {
        url = `${process.env.VUE_APP_API_URL}${url}`;
        await precacheURL(url);
        console.log('precached', url);
      });
    },
    async getDynamicLinks() {
      const date = new Date();
      date.setDate(date.getDate() - 4)
      for (let i = 0; i < 31; i++) {
        date.setDate(date.getDate() + 1);
        const date_str = date.getFullYear() + '-' + (date.getMonth() + 1) + '-' + date.getDate();
        console.log(date_str);
        await valid_daily_offices.forEach(async (office) => {
          await precacheURL(await getOfficeURL(office, 'office', date_str));
        });
        await valid_family_offices.forEach(async (office) => {
          await precacheURL(await getOfficeURL(office, 'family', date_str));
        });
        this.syncedUntil = date_str;
      }
    },
    async syncDynamicLink(date, link) {

    },
    async sync() {
      const status = await Network.getStatus();
      if (!status.connected) {
        return
      }
      await this.syncAlwaysSyncLinks();
      const links = await this.getDynamicLinks();
      console.log(links);
    },
  },
};
</script>
