import Bugsnag from '@bugsnag/js';
import BugsnagPluginVue from '@bugsnag/plugin-vue';
import { Capacitor } from '@capacitor/core';
import { version as appVersion } from '../../package.json';

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
// A browser quirk, not a bug: the observer simply skipped a frame.
const RESIZE_OBSERVER = /ResizeObserver loop/i;
const EXTENSION_FILE =
  /^(chrome|moz|safari|safari-web|ms-browser)-extension:\/\//i;
// Requests that never reached the server (offline, timed out, cancelled).
const NETWORK_CODES = new Set(['ERR_NETWORK', 'ECONNABORTED', 'ERR_CANCELED']);

let started = false;

/** Whether this report is noise to drop rather than a bug in the app. */
export function isNoise(event) {
  const error = event.errors?.[0];
  if (!error) return false;
  const text = `${error.errorClass || ''}: ${error.errorMessage || ''}`;
  if (STALE_CHUNK.test(text) || RESIZE_OBSERVER.test(text)) return true;
  if ((error.stacktrace || []).some((f) => EXTENSION_FILE.test(f.file || ''))) {
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
