/* global process */
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  server: {
    port: 5176,
    strictPort: true,
  },
  plugins: [vue()],
  build: {
    // Maps for Bugsnag, without the sourceMappingURL comment in the shipped
    // files. deploy/deploy.sh uploads them and removes them from dist before
    // publishing (scripts/upload-sourcemaps.mjs), so they are never public.
    sourcemap: 'hidden',
  },
  resolve: {
    alias: {
      '@': path.resolve(process.cwd(), './src'), // Replaced __dirname for ESM compatibility
    },
  },
});
