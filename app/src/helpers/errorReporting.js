import Bugsnag from '@bugsnag/js';
import BugsnagPluginVue from '@bugsnag/plugin-vue';
import { Capacitor } from '@capacitor/core';
import { version as packageVersion } from '../../package.json';

// The deploy stamps each web build (package version + commit) so reports and
// uploaded source maps match; other builds report the package version.
const appVersion = import.meta.env.VITE_APP_VERSION || packageVersion;

/*
  Error reporting
  ===============
  Uncaught exceptions, unhandled promise rejections, and Vue component
  errors go to Bugsnag, along with anything sent through notify().

  Reporting is on only when VITE_BUGSNAG_ENABLED is "true" and
  VITE_BUGSNAG_API_KEY is set: on in production builds (.env.production),
  off in development (.env.development). Otherwise Bugsnag never starts and
  every function here does nothing, so tests need no setup. Components use
  this module rather than Bugsnag directly.
*/

// Reports are sent only from these release stages.
const REPORTING_STAGES = ['production', 'staging'];

// The app already reloads when a page chunk from an older build is missing
// (see `vite:preloadError` in main.js), so these aren't worth reporting.
const STALE_CHUNK =
  /ChunkLoadError|Loading chunk \S+ failed|Failed to fetch dynamically imported module|Importing a module script failed|error loading dynamically imported module|Unable to preload CSS/i;
// When a route's chunk fails to load, the `vite:preloadError` handler cancels
// the error and reloads, so the import resolves to nothing and vue-router
// raises this just before the reload. Same stale-chunk case as above.
const EMPTY_ROUTE_CHUNK = /Couldn't resolve component "default" at/i;
// A browser quirk, not a bug: the observer simply skipped a frame.
const RESIZE_OBSERVER = /ResizeObserver loop/i;
const EXTENSION_FILE =
  /^(chrome|moz|safari|safari-web|ms-browser)-extension:\/\//i;
// Extension errors that arrive with no stack, so EXTENSION_FILE can't match.
// The app itself never calls the extension messaging API.
const EXTENSION_MESSAGE = /Invalid call to runtime\.sendMessage\(\)/i;
// Our built page has one short inline script, wrapped in try/catch, so errors
// whose every frame is in the page document itself come from a script the
// browser or an extension injected (translation, reader and in-app browsers
// on iOS): e.g. "Maximum call stack size exceeded" recursing between two
// minified functions at line 400+ of /commemorations/<id>.
function onlyInPageDocument(frames) {
  let page;
  try {
    const { origin, pathname } = window.location;
    page = origin + pathname;
  } catch {
    return false;
  }
  const stripped = (file) => String(file || '').split(/[?#]/)[0];
  return (
    frames.some((f) => stripped(f.file) === page) &&
    frames.every((f) => !f.file || stripped(f.file) === page)
  );
}
// A fetch() that never got a response (offline, dropped connection, blocker)
// rejects with a bare TypeError: "Load failed" in Safari, "Failed to fetch" in
// Chrome, "NetworkError ..." in Firefox. Vite's modulepreload polyfill (for
// browsers without <link rel="modulepreload">) fetches upcoming chunks this way
// and never handles the failure; the real import, if it fails too, is caught as
// STALE_CHUNK. So drop it only when it has no stack frame and the last failed
// fetch was one of our own built assets. Other fetches (Firebase, Capacitor
// plugins) failing the same way may be an outage, so they are still reported.
const BARE_NETWORK_FAILURE =
  /^TypeError: (Load failed|Failed to fetch|NetworkError when attempting to fetch resource\.?)$/i;
// Requests that never reached the server (offline, timed out, cancelled).
const NETWORK_CODES = new Set(['ERR_NETWORK', 'ECONNABORTED', 'ERR_CANCELED']);

let started = false;

/** Whether the most recent failed fetch() was for one of our built assets. */
function lastFailedFetchWasOwnAsset(event) {
  const failed = (event.breadcrumbs || [])
    .filter((b) => b.type === 'request' && b.message === 'fetch() error')
    .pop();
  const url = failed?.metadata?.url;
  if (!url) return false;
  try {
    const { origin, pathname } = new window.URL(url, window.location.href);
    return origin === window.location.origin && pathname.startsWith('/assets/');
  } catch {
    return false;
  }
}

/** Whether this report is noise to drop rather than a bug in the app. */
export function isNoise(event) {
  const error = event.errors?.[0];
  if (!error) return false;
  const text = `${error.errorClass || ''}: ${error.errorMessage || ''}`;
  if (
    STALE_CHUNK.test(text) ||
    EMPTY_ROUTE_CHUNK.test(text) ||
    RESIZE_OBSERVER.test(text) ||
    EXTENSION_MESSAGE.test(text)
  )
    return true;
  const frames = error.stacktrace || [];
  if (
    BARE_NETWORK_FAILURE.test(text) &&
    frames.every((f) => !f.file || f.file === 'unknown file') &&
    lastFailedFetchWasOwnAsset(event)
  )
    return true;
  if (onlyInPageDocument(frames)) return true;
  if (frames.some((f) => EXTENSION_FILE.test(f.file || ''))) {
    return true;
  }
  const original = event.originalError;
  return Boolean(
    original?.isAxiosError &&
    NETWORK_CODES.has(original.code) &&
    !original.response
  );
}

/**
 * Start Bugsnag and catch errors from the Vue app. Call once, before the
 * app mounts. Does nothing unless reporting is enabled and has a key.
 */
export function startErrorReporting(app) {
  const apiKey = import.meta.env.VITE_BUGSNAG_API_KEY;
  const enabled = import.meta.env.VITE_BUGSNAG_ENABLED === 'true';
  if (started || !enabled || !apiKey) return false;
  try {
    Bugsnag.start({
      apiKey,
      appVersion,
      appType: Capacitor.getPlatform(),
      releaseStage:
        import.meta.env.VITE_BUGSNAG_RELEASE_STAGE || import.meta.env.MODE,
      enabledReleaseStages: REPORTING_STAGES,
      collectUserIp: false,
      // The anonymous client id stands in for the user (see identifyUser).
      generateAnonymousId: false,
      plugins: [new BugsnagPluginVue()],
      onError: (event) => !isNoise(event),
    });
    app?.use(Bugsnag.getPlugin('vue'));
    started = true;
  } catch {
    // Reporting must never stop the app from starting.
  }
  return started;
}

/** Tag reports with the app's anonymous client id (never an email). */
export function identifyUser(clientId) {
  if (!started || !clientId) return;
  Bugsnag.setUser(String(clientId));
}

/**
 * Report a handled error. `metadata` is a map of tab name → values, shown
 * as tabs on the report in Bugsnag. Options: `context`, `severity`
 * ('error' | 'warning' | 'info'), and `groupingHash` to group reports
 * together regardless of where they were raised.
 */
export function notify(error, metadata = {}, options = {}) {
  if (!started) {
    if (import.meta.env.DEV && import.meta.env.MODE !== 'test') {
      // eslint-disable-next-line no-console
      console.warn('[error report, not sent]', error, metadata);
    }
    return false;
  }
  try {
    Bugsnag.notify(error, (event) => {
      Object.entries(metadata).forEach(([section, values]) => {
        event.addMetadata(section, values);
      });
      if (options.context) event.context = options.context;
      if (options.severity) event.severity = options.severity;
      if (options.groupingHash) event.groupingHash = options.groupingHash;
    });
    return true;
  } catch {
    return false;
  }
}

// Keys already reported in this page load.
const reportedKeys = new Set();

/**
 * notify(), but at most once per browser session for the given key, so a
 * condition that repeats (every relayout, every open) is reported once.
 */
export function notifyOnce(key, error, metadata, options) {
  if (reportedKeys.has(key)) return false;
  reportedKeys.add(key);
  const storageKey = `reported:${key}`;
  try {
    if (window.sessionStorage.getItem(storageKey)) return false;
    window.sessionStorage.setItem(storageKey, String(Date.now()));
  } catch {
    // Storage blocked: once per page load will do.
  }
  return notify(error, metadata, options);
}
