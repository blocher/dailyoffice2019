import { createApp } from "vue";

import store from "./store";
import axios from "axios";
import VueAxios from "vue-axios";
import App from "./App.vue";
import router from "./router";
import ElementPlus from "element-plus";
import "./assets/tailwind.css";
import "element-plus/dist/index.css";
import "element-plus/theme-chalk/dark/css-vars.css";

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
  faBookBible,
  faCircle1,
  faCircle2,
  faCircle3,
  faCircle4,
  faCopy,
  faEnvelopes,
  faFontCase,
  faLeft,
  faMessagePen,
  faMoonStars,
  faOctagonCheck,
  faRight,
  faSearch,
  faShareNodes,
  faSquareCaretDown,
  faSquareCaretUp,
  faSquareUpRight,
  faSun,
  faSunrise,
  faSunset,
} from "@fortawesome/pro-duotone-svg-icons";
import VueGtag from "vue-gtag";
import { faFacebook } from "@fortawesome/free-brands-svg-icons";

library.add(
  faSun,
  faSunrise,
  faSunset,
  faMoonStars,
  faLeft,
  faRight,
  faFontCase,
  faShareNodes,
  faCopy,
  faFacebook,
  faEnvelopes,
  faBookBible,
  faMessagePen,
  faCircle1,
  faCircle2,
  faCircle3,
  faCircle4,
  faSearch,
  faSquareUpRight,
  faSquareCaretUp,
  faSquareCaretDown,
  faOctagonCheck
);

router.beforeEach((to, from, next) => {
  // This goes through the matched routes from last to first, finding the closest route with a title.
  // e.g., if we have `/some/deep/nested/route` and `/some`, `/deep`, and `/nested` have titles,
  // `/nested`'s will be chosen.
  const nearestWithTitle = to.matched
    .slice()
    .reverse()
    .find((r) => r.meta && r.meta.title);

  // Find the nearest route element with meta tags.
  const nearestWithMeta = to.matched
    .slice()
    .reverse()
    .find((r) => r.meta && r.meta.metaTags);

  const previousNearestWithMeta = from.matched
    .slice()
    .reverse()
    .find((r) => r.meta && r.meta.metaTags);

  // If a route with a title was found, set the document (page) title to that value.
  if (nearestWithTitle) {
    document.title = nearestWithTitle.meta.title;
  } else if (previousNearestWithMeta) {
    document.title = previousNearestWithMeta.meta.title;
  }

  // Remove any stale meta tags from the document using the key attribute we set below.
  Array.from(document.querySelectorAll("[data-vue-router-controlled]")).map(
    (el) => el.parentNode.removeChild(el)
  );

  // Skip rendering meta tags if there are none.
  if (!nearestWithMeta) return next();

  // Turn the meta tag definitions into actual elements in the head.
  nearestWithMeta.meta.metaTags
    .map((tagDef) => {
      const tag = document.createElement("meta");

      Object.keys(tagDef).forEach((key) => {
        tag.setAttribute(key, tagDef[key]);
      });

      // We use this to track which meta tags we create so we don't interfere with other ones.
      tag.setAttribute("data-vue-router-controlled", "");

      return tag;
    })
    // Add the meta tags to the document head.
    .forEach((tag) => document.head.appendChild(tag));

  next();
});

const app = createApp(App)
  .use(router)
  .use(
    VueGtag,
    {
      appName: "The Daily Office (Beta)",
      pageTrackerScreenviewEnabled: true,
      config: { id: "G-NPCDSDW90W" },
    },
    router
  )
  .use(store)
  .use(VueAxios, axios)
  .use(ElementPlus)
  .component("font-awesome-icon", FontAwesomeIcon);

router.isReady().then(() => {
  app.mount("#app");
});
