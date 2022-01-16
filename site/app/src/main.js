import { createApp } from "vue";

import "./registerServiceWorker";

import store from "./store";
import axios from "axios";
import VueAxios from "vue-axios";
import App from "./App.vue";
import router from "./router";

const app = createApp(App).use(store).use(router).use(VueAxios, axios);

router.isReady().then(() => {
  app.mount("#app");
});
