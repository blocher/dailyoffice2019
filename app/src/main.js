/* eslint-disable no-console */
import { createApp } from 'vue';

import store from './store';
import axios from 'axios';
import VueAxios from 'vue-axios';
import App from './App.vue';
import router from './router';
import UiKit from './ui';
import './styles/index.css';
import { createMetaManager } from 'vue-meta';
import { installViewportCssVars } from './helpers/viewport';
import { getClientId } from './helpers/clientId';
import { loadDisplayPreferences } from './helpers/displayPreferences';
import { loadDiscovery } from './helpers/discovery';
import { requestBookView } from './helpers/panels';
import { createGtag, event } from 'vue-gtag';
import { FirebaseAnalytics } from '@capacitor-firebase/analytics';
import { Capacitor } from '@capacitor/core';

// Stabilize viewport units on mobile browsers (notably iOS Chrome) where
// the browser toolbars collapsing/expanding can cause fixed footers to “float”.
installViewportCssVars();

// After a deploy, an open tab may ask for a page chunk that no longer
// exists. Reload to pick up the new build (at most once a minute, so a
// chunk that is truly missing can't cause a reload loop).
window.addEventListener('vite:preloadError', (event) => {
  try {
    const last = Number(window.sessionStorage.getItem('reloadedForNewBuild'));
    if (Date.now() - last < 60000) return;
    window.sessionStorage.setItem('reloadedForNewBuild', String(Date.now()));
  } catch {
    return;
  }
  event.preventDefault();
  window.location.reload();
});

router.beforeEach((to, from) => {
  // ?book=1 opens an office in book view. Take the flag off the address
  // before the page renders, so closing the book doesn't reload the office.
  if (to.query.book) {
    requestBookView();
    const query = { ...to.query };
    delete query.book;
    return { path: to.path, query, hash: to.hash, replace: true };
  }
  // A navigation to the same address (e.g. Back closing the book view)
  // changes nothing on the page.
  if (from.matched.length && to.fullPath === from.fullPath) return;
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

    // Update Open Graph title
    updateMetaTag('property', 'og:title', nearestWithTitle.meta.title);
    updateMetaTag('name', 'twitter:title', nearestWithTitle.meta.title);
  } else if (previousNearestWithMeta) {
    document.title = previousNearestWithMeta.meta.title;
    updateMetaTag('property', 'og:title', previousNearestWithMeta.meta.title);
    updateMetaTag('name', 'twitter:title', previousNearestWithMeta.meta.title);
  }

  // Update Open Graph URL
  updateMetaTag('property', 'og:url', window.location.href);

  // Remove any stale meta tags from the document using the key attribute we set below.
  Array.from(document.querySelectorAll('[data-vue-router-controlled]')).map(
    (el) => el.parentNode.removeChild(el)
  );

  // Skip rendering meta tags if there are none.
  if (!nearestWithMeta) return;

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
});

// Helper function to update meta tags
function updateMetaTag(attribute, value, content) {
  let metaTag = document.querySelector(`meta[${attribute}="${value}"]`);
  if (metaTag) {
    metaTag.setAttribute('content', content);
  } else {
    metaTag = document.createElement('meta');
    metaTag.setAttribute(attribute, value);
    metaTag.setAttribute('content', content);
    document.head.appendChild(metaTag);
  }
}

router.afterEach(async (to, from) => {
  if (!Capacitor.isNativePlatform()) return;
  if (from.matched.length && to.fullPath === from.fullPath) return;
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
  .use(UiKit)
  .use(createMetaManager());

app.config.globalProperties.$gtag = { event };

const bootstrap = async () => {
  await loadDisplayPreferences();
  loadDiscovery();
  // Attach the anonymous client id + platform to every API request so the
  // backend can attribute office views to a unique user (updated clients only).
  try {
    const clientId = await getClientId();
    axios.defaults.headers.common['X-Client-Id'] = clientId;
    axios.defaults.headers.common['X-Client-Platform'] =
      Capacitor.getPlatform();
  } catch {
    // analytics headers are best-effort
  }
  await router.isReady();
  app.mount('#app');
};

bootstrap();
