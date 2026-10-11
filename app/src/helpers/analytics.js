import axios from 'axios';
import { Capacitor } from '@capacitor/core';
import { event as gtagEvent } from 'vue-gtag';
import { FirebaseAnalytics } from '@capacitor-firebase/analytics';
import { getClientId } from './clientId';

// Emits a usage event. Depending on the flags it can:
//   - POST to our own backend (source of truth for the self-hosted dashboard)
//   - Mirror to Google Analytics (web) / Firebase (native)
// The same anonymous client id is attached everywhere so both dashboards agree
// on unique users. All failures are swallowed: analytics must never break the UI.
export async function trackEvent(
  name,
  payload = {},
  { toBackend = false, toGA = true } = {}
) {
  let clientId = null;
  try {
    clientId = await getClientId();
  } catch {
    clientId = null;
  }
  const platform = Capacitor.getPlatform();
  const params = { ...payload, client_id: clientId, platform };

  if (toBackend) {
    try {
      await axios.post(
        `${import.meta.env.VITE_API_URL}api/v1/analytics/event`,
        { event_type: name, ...params }
      );
    } catch {
      // ignore
    }
  }

  if (toGA) {
    try {
      if (Capacitor.isNativePlatform()) {
        await FirebaseAnalytics.logEvent({ name, params });
      } else {
        gtagEvent(name, params);
      }
    } catch {
      // ignore
    }
  }
}
