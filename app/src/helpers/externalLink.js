import { Browser } from '@capacitor/browser';

/**
 * Open a link in the in-app browser. The Android bridge rejects with "Unable
 * to display URL" when the device has no browser able to show it (a missing or
 * disabled WebView/Chrome, a managed profile), so fall back to the window
 * opener instead of leaving the tap with no effect and an unhandled rejection.
 */
export async function openExternalLink(url) {
  try {
    await Browser.open({ url });
  } catch {
    window.open(url, '_blank', 'noopener,noreferrer');
  }
}
