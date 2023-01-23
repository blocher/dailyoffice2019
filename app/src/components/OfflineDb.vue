<template>
  <h3>Database sync util: {{ content }}</h3>
</template>


<script>

import {getCurrentInstance} from 'vue';
import {createTablesNoEncryption} from '@/utils/utils-db-no-encryption';
import {precacheURL} from "@/utils/request";
import {Network} from "@capacitor/network";

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
export default {
  data() {
    return {
      content: 'starting',
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
    async sync() {
      const status = await Network.getStatus();
      if (!status.connected) {
        return
      }
      const date = new Date();
      const chckDates = [];
      for (let i = 0; i < 90; i++) {
        date.setDate(date.getDate() + 1);
        chckDates.push(new Date(date.getTime()));
      }
      // console.log(chckDates);
      alwaysSync.forEach(async (url) => {
        url = `${process.env.VUE_APP_API_URL}${url}`;
        await precacheURL(url);
        console.log('precached', url)
      });

    }
  },
};
</script>
