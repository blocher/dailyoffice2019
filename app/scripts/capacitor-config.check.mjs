import assert from 'node:assert/strict';
import test from 'node:test';
import { loadConfig } from '@capacitor/cli/dist/config.js';

test('Capacitor loads the TypeScript configuration', async () => {
  const config = await loadConfig();

  assert.equal(config.app.extConfigType, 'ts');
  assert.equal(config.app.appId, 'com.dailyoffice.dailyoffice2019');
  assert.equal(config.app.appName, 'daily_office');
  assert.equal(config.app.webDir, 'dist');
});

test('The splash screen always hides by itself', async () => {
  const config = await loadConfig();
  const splash = config.app.extConfig.plugins.SplashScreen;

  // main.js hides it after the first render; this is the fallback, so a slow
  // or failed start can never leave someone stuck on the cover art.
  assert.equal(splash.launchAutoHide, true);
  assert.ok(splash.launchShowDuration <= 5000);
});
