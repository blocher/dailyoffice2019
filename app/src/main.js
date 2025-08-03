/* eslint-disable no-console */
import { createApp } from 'vue';

import store from './store';
import axios from 'axios';
import VueAxios from 'vue-axios';
import App from './App.vue';
import router from './router';
import ElementPlus from 'element-plus';
import './assets/tailwind.css';
import 'element-plus/dist/index.css';
import 'element-plus/theme-chalk/dark/css-vars.css';

import { library } from '@fortawesome/fontawesome-svg-core';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
import { createMetaManager } from 'vue-meta';

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
  faBooks,
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
} from '@fortawesome/pro-duotone-svg-icons';
import { createGtag, event } from 'vue-gtag';
import { faFacebook } from '@fortawesome/free-brands-svg-icons';
import { FirebaseAnalytics } from '@capacitor-firebase/analytics';
import { Capacitor } from '@capacitor/core';

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
  faBooks,
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
  Array.from(document.querySelectorAll('[data-vue-router-controlled]')).map(
    (el) => el.parentNode.removeChild(el)
  );

  // Skip rendering meta tags if there are none.
  if (!nearestWithMeta) return next();

  // Turn the meta tag definitions into actual elements in the head.
  nearestWithMeta.meta.metaTags
    .map((tagDef) => {
      const tag = document.createElement('meta');

      Object.keys(tagDef).forEach((key) => {
        tag.setAttribute(key, tagDef[key]);
      });

      // We use this to track which meta tags we create so we don't interfere with other ones.
      tag.setAttribute('data-vue-router-controlled', '');

      return tag;
    })
    // Add the meta tags to the document head.
    .forEach((tag) => document.head.appendChild(tag));

  next();
});

router.afterEach(async (to, from) => {
  if (!Capacitor.isNativePlatform()) return;
  const screenName = typeof to.name === 'string' ? to.name : to.path;
  const prevScreen = typeof from.name === 'string' ? from.name : from.path;
  const params = Object.keys(to.params || {}).length
    ? JSON.stringify(to.params)
    : undefined;
  const query = Object.keys(to.query || {}).length
    ? JSON.stringify(to.query)
    : undefined;
  try {
    await FirebaseAnalytics.setCurrentScreen({
      screenName,
      screenClassOverride: screenName,
    });
    console.log('FirebaseAnalytics setCurrentScreen', {
      screenName,
      screenClassOverride: screenName,
    });
  } catch (err) {
    console.error('FirebaseAnalytics setCurrentScreen error', err);
  }
  try {
    await FirebaseAnalytics.logEvent({
      name: 'screen_view',
      params: {
        screen_name: screenName,
        screen_class: screenName,
        page_path: to.fullPath,
        page_title: to.meta?.title || document.title,
        previous_screen_name: prevScreen,
        previous_screen_class: prevScreen,
        ...(params ? { screen_params: params } : {}),
        ...(query ? { screen_query: query } : {}),
      },
    });
    console.log('FirebaseAnalytics logEvent', {
      event: 'screen_view',
      screenName,
      path: to.fullPath,
      params,
      query,
    });
  } catch (err) {
    console.error('FirebaseAnalytics logEvent error', err);
  }
});

const app = createApp(App)
  .use(router)
  .use(
    createGtag({
      tagId: 'G-NPCDSDW90W',
      config: {
        send_page_view: false, // we'll handle pageviews manually via router
      },
      // Auto-track using the Vue router
      pageTracker: {
        router,
        useScreenview: false,
        // Example: exclude admin pages
        exclude: (to) => to.meta.noAnalytics === true,
        // Template lets you customize the payload per route
        template: (to) => ({
          page_path: to.fullPath,
          page_title: to.meta.title || document.title,
        }),
      },
    })
  )
  .use(store)
  .use(VueAxios, axios)
  .use(ElementPlus)
  .use(createMetaManager())
  .component('font-awesome-icon', FontAwesomeIcon);

app.config.globalProperties.$gtag = { event };

router.isReady().then(() => {
  app.mount('#app');
});
