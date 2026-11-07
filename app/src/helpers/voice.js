/*
  Siri, Google Assistant and Gemini
  =================================
  The native apps answer voice requests by opening a page (iOS App Intents in
  ios/App/App/Voice/, Android shortcuts and AppFunctions in
  android/.../voice/). Each one names an address in the app:

    dailyoffice2019://open/office/compline?autoplay=1
    dailyoffice2019://open/family/morning_prayer
    dailyoffice2019://open/readings/holy_eucharist/?autoplay=1
    dailyoffice2019://open/psalm/23/

  The path after the host is the app's own route; a web address on
  dailyoffice2019.com works the same way. ?autoplay=1 starts the page's
  audio once it is ready, as if the listener had pressed Play.

  Back the other way, pages tell the native app what the listener just opened
  or played (donateActivity), so Siri Suggestions and Android's shortcut
  suggestions learn when someone prays, and Siri knows what is on screen.
*/
import { reactive } from 'vue';
import { Capacitor, registerPlugin } from '@capacitor/core';
import { App } from '@capacitor/app';

const VoiceLaunch = registerPlugin('VoiceLaunch');

const WEB_HOSTS = [
  'dailyoffice2019.com',
  'www.dailyoffice2019.com',
  'app.dailyoffice2019.com',
];

// An autoplay request lasts this long: enough for a cold start and a slow
// office download, not so long that a later visit starts playing by itself.
export const AUTOPLAY_WINDOW_MS = 2 * 60 * 1000;

// The page an ?autoplay=1 address asked to play, and when.
export const autoplayRequest = reactive({ path: null, at: 0 });

/*
  The app route a launch address names, or null when it isn't one of ours.
  dailyoffice2019://open/office/compline   -> /office/compline
  dailyoffice2019://office/compline        -> /office/compline
  https://www.dailyoffice2019.com/psalm/23 -> /psalm/23
*/
export function pathFromLaunchUrl(url) {
  if (!url || typeof url !== 'string') return null;
  // Parsed by hand: older WebViews don't give custom schemes a host.
  const custom = url.match(
    /^dailyoffice2019:(?:\/\/)?([^?#]*)([?][^#]*)?(#.*)?$/i
  );
  let path;
  let search;
  let hash;
  if (custom) {
    const [first, ...rest] = custom[1].split('/');
    path = first === 'open' ? `/${rest.join('/')}` : `/${custom[1]}`;
    search = custom[2] || '';
    hash = custom[3] || '';
  } else {
    let parsed;
    try {
      parsed = new window.URL(url);
    } catch {
      return null;
    }
    if (
      !['http:', 'https:'].includes(parsed.protocol) ||
      !WEB_HOSTS.includes(parsed.hostname)
    ) {
      return null;
    }
    path = parsed.pathname;
    search = parsed.search;
    hash = parsed.hash;
  }
  // Trailing slashes stay: some routes (/psalm/23/) are declared with one.
  path = path.replace(/\/{2,}/g, '/');
  return `${path}${search}${hash}`;
}

export function requestAutoplay(path, now = Date.now()) {
  autoplayRequest.path = normalizePath(path);
  autoplayRequest.at = now;
}

// True, once, when the page at this path was asked to play. Pages call it
// when they load.
export function takeAutoplayRequest(path, now = Date.now()) {
  if (!autoplayRequest.path) return false;
  const fresh = now - autoplayRequest.at <= AUTOPLAY_WINDOW_MS;
  const match = autoplayRequest.path === normalizePath(path);
  if (!fresh) clearAutoplayRequest();
  if (!fresh || !match) return false;
  clearAutoplayRequest();
  return true;
}

export function clearAutoplayRequest() {
  autoplayRequest.path = null;
  autoplayRequest.at = 0;
}

function normalizePath(path) {
  if (!path) return '/';
  const trimmed = path.replace(/\/+$/, '');
  return trimmed || '/';
}

// For a route with ?autoplay=1: notes the request and returns where to go
// instead, without the flag (like ?book=1 in helpers/panels.js), so reloading
// or going Back to the page doesn't start the audio again.
export function takeAutoplayQuery(to) {
  if (!to.query.autoplay) return null;
  const query = { ...to.query };
  const wanted = query.autoplay;
  delete query.autoplay;
  if (wanted !== '0' && wanted !== 'false') requestAutoplay(to.path);
  return { path: to.path, query, hash: to.hash, replace: true };
}

/*
  Listens for addresses the native app is opened with (links, home-screen
  shortcuts, Android voice actions: the App plugin's appUrlOpen) and for
  Siri's App Intents (the VoiceLaunch plugin), and goes to each one's page.
*/
export function installVoiceLaunch(router) {
  if (!Capacitor.isNativePlatform()) return;
  let last = { path: null, at: 0 };
  const go = (url, path = pathFromLaunchUrl(url)) => {
    if (!path) return;
    // A cold start can report the same address twice (the launch URL and an
    // appUrlOpen event).
    const now = Date.now();
    if (last.path === path && now - last.at < 3000) return;
    last = { path, at: now };
    router.push(path).catch(() => {});
  };
  App.addListener('appUrlOpen', (event) => go(event?.url)).catch(() => {});
  App.getLaunchUrl()
    .then((result) => go(result?.url))
    .catch(() => {});
  VoiceLaunch.addListener('open', (event) =>
    go(event?.url, event?.path || pathFromLaunchUrl(event?.url))
  ).catch(() => {});
}

/*
  Tells the native app what the listener opened or played, for Siri
  Suggestions, onscreen awareness and Android's shortcut suggestions.
    { kind: 'office', serviceType: 'office'|'family', office, date, title,
      played }
    { kind: 'readings', service, date, title, played }
    { kind: 'psalm', number, title }
  Best-effort: nothing happens on the web or in older app builds.
*/
export function donateActivity(activity) {
  if (!Capacitor.isNativePlatform()) return;
  if (!Capacitor.isPluginAvailable('VoiceLaunch')) return;
  VoiceLaunch.donate(activity).catch(() => {});
}
