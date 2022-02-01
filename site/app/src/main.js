import { createApp } from "vue";

import "./registerServiceWorker";

import store from "./store";
import axios from "axios";
import VueAxios from "vue-axios";
import App from "./App.vue";
import router from "./router";

import { library } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";

// import { faTwitter } from "@fortawesome/free-brands-svg-icons";
// import { faUserSecret } from "@fortawesome/free-solid-svg-icons";
// import {
//   faMoonStars,
//   faSun,
//   faSunrise,
//   faSunset,
// } from "@fortawesome/pro-regular-svg-icons";
// import { faCoffee } from "@fortawesome/pro-light-svg-icons";
// import { faFeather } from "@fortawesome/pro-thin-svg-icons";
import {
  faLeft,
  faMoonStars,
  faRight,
  faSun,
  faSunrise,
  faSunset,
} from "@fortawesome/pro-duotone-svg-icons";

library.add(faSun, faSunrise, faSunset, faMoonStars, faLeft, faRight);

const app = createApp(App)
  .use(store)
  .use(router)
  .use(VueAxios, axios)
  .component("font-awesome-icon", FontAwesomeIcon);

router.isReady().then(() => {
  app.mount("#app");
});
