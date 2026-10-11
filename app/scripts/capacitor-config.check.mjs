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
