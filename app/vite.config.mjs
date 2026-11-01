/* global process */
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import path from 'path';
import fs from 'fs';
import crypto from 'crypto';

/*
  Writes dist/sw.js from src/offline/serviceWorker.js, filling in the files
  to keep for offline use (the app shell) and a version that changes with
  them. The Caslon faces and icons come from public/; the other typefaces
  are cached the first time they're used. See src/offline/pwa.js.
*/
function offlineServiceWorker() {
  let outDir;
  let root;
  return {
    name: 'offline-service-worker',
    apply: 'build',
    configResolved(config) {
      root = config.root;
      outDir = path.resolve(config.root, config.build.outDir);
    },
    writeBundle(_options, bundle) {
      // Scripts, styles, and the images they use (not the alternative
      // typefaces' many font files, which are cached when first used).
      const built = Object.keys(bundle).filter((file) =>
        /\.(js|css|png|jpe?g|svg|webp)$/.test(file)
      );
      const fromPublic = [
        'site.webmanifest',
        'favicon.ico',
        'favicon-32x32.png',
        'apple-touch-icon.png',
        'android-chrome-192x192.png',
        'android-chrome-512x512.png',
        'maskable-512x512.png',
        ...fs
          .readdirSync(path.join(outDir, 'assets/fonts'))
          .filter((file) => file.endsWith('.woff2'))
          .map((file) => `assets/fonts/${file}`),
      ].filter((file) => fs.existsSync(path.join(outDir, file)));
      const precache = ['/', ...[...built, ...fromPublic].sort().map((f) => `/${f}`)];
      const version = crypto
        .createHash('sha256')
        .update(precache.join('\n'))
        .update(fs.readFileSync(path.join(outDir, 'index.html')))
        .digest('hex')
        .slice(0, 12);
      const template = fs.readFileSync(
        path.join(root, 'src/offline/serviceWorker.js'),
        'utf8'
      );
      const source = template
        .replace("'__VERSION__'", JSON.stringify(version))
        .replace(
          'const PRECACHE = __PRECACHE__;',
          `const PRECACHE = ${JSON.stringify(precache, null, 2)};`
        );
      if (source.includes('= __PRECACHE__')) {
        throw new Error('offline-service-worker: precache list not filled in');
      }
      fs.writeFileSync(path.join(outDir, 'sw.js'), source);
    },
  };
}

// https://vitejs.dev/config/
export default defineConfig({
  server: {
    port: 5176,
    strictPort: true,
  },
  plugins: [vue(), offlineServiceWorker()],
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
