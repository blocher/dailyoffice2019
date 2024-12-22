import { defineConfig } from 'cypress';
import plugins from './tests/e2e/plugins/index.js';

export default defineConfig({
  e2e: {
    setupNodeEvents(on, config) {
      // This replaces the `pluginsFile` option
      return plugins(on, config);
    },
    specPattern: 'tests/e2e/**/*.{js,jsx,ts,tsx}',
    supportFile: 'tests/e2e/support/index.js',
    baseUrl: 'http://localhost:5173/',
    retryOnNetworkFailure: true,
    retryOnStatusCodeFailure: true,
    experimentalSourceRewriting: true,
  },
});
