/* global process */
import { defineConfig, loadEnv } from 'vite';
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
// With VITE_SERVICE_WORKER=false: a worker that takes itself away. Browsers
// keep a worker until its script changes; this one empties its caches,
// unregisters, and reloads the open pages from the network.
const REMOVE_SERVICE_WORKER = `self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (event) => {
  event.waitUntil(
    (async () => {
      const names = await caches.keys();
      await Promise.all(names.map((name) => caches.delete(name)));
      await self.registration.unregister();
      const windows = await self.clients.matchAll({ type: 'window' });
      windows.forEach((client) => client.navigate(client.url));
    })()
  );
});
`;

function offlineServiceWorker() {
  let outDir;
  let root;
  let disabled = false;
  return {
    name: 'offline-service-worker',
    apply: 'build',
    configResolved(config) {
      root = config.root;
      outDir = path.resolve(config.root, config.build.outDir);
      disabled =
        loadEnv(config.mode, config.envDir || root, 'VITE_')
          .VITE_SERVICE_WORKER === 'false';
    },
    writeBundle(_options, bundle) {
      if (disabled) {
        fs.writeFileSync(path.join(outDir, 'sw.js'), REMOVE_SERVICE_WORKER);
        return;
      }
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
      const precache = [
        '/',
        ...[...built, ...fromPublic].sort().map((f) => `/${f}`),
      ];
      // The files' contents, not just their names: public/ files keep their
      // names when they change (the manifest, an icon, a font).
      const hash = crypto.createHash('sha256').update(precache.join('\n'));
      ['index.html', ...built, ...fromPublic].forEach((file) =>
        hash.update(fs.readFileSync(path.join(outDir, file)))
      );
      const version = hash.digest('hex').slice(0, 12);
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
