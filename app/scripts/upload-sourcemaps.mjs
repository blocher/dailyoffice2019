/*
  Upload the build's source maps to Bugsnag, then remove them from dist.

    node scripts/upload-sourcemaps.mjs [--base-url <origin>]...

  `vite build` writes hidden source maps (no sourceMappingURL comment; see
  vite.config.mjs). deploy/deploy.sh runs this before publishing dist, and
  `npm run capacitor:build` before `cap sync`, so the maps reach Bugsnag but
  never the public site or the app bundles. The .map files are deleted
  even when there is nothing to upload to.

  Bugsnag matches a report to a map by the file's URL and the app version,
  so maps are uploaded once per origin the bundle is served from (the web
  site by default; pass --base-url for the native apps) with the version the
  build reports: VITE_APP_VERSION when the deploy sets it, otherwise the
  package version (see src/helpers/errorReporting.js).

  The key and on/off switch are the app's own: VITE_BUGSNAG_API_KEY and
  VITE_BUGSNAG_ENABLED from the environment or app/.env.production(.local).
  BUGSNAG_SOURCE_MAP_ENDPOINT overrides the upload server (default
  https://upload.bugsnag.com). A failed upload is reported but doesn't fail
  the deploy.
*/
/* global process, console */
import { readdir, readFile, rm } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadEnv } from 'vite';
import { browser } from '@bugsnag/source-maps';

const APP_DIR = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const DIST = path.join(APP_DIR, 'dist');
const WEB_ORIGINS = [
  'https://www.dailyoffice2019.com',
  'https://dailyoffice2019.com',
];

async function mapFiles(directory) {
  const entries = await readdir(directory, {
    recursive: true,
    withFileTypes: true,
  });
  return entries
    .filter((entry) => entry.isFile() && entry.name.endsWith('.map'))
    .map((entry) => path.join(entry.parentPath ?? entry.path, entry.name));
}

function baseUrls(argv) {
  const urls = [];
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === '--base-url' && argv[i + 1]) urls.push(argv[(i += 1)]);
  }
  return urls.length ? urls : WEB_ORIGINS;
}

// The uploader logs every file; keep only its warnings and errors.
const logger = {
  trace() {},
  debug() {},
  info() {},
  success() {},
  warn: (...args) => console.warn(...args),
  error: (...args) => console.error(...args),
  fatal: (...args) => console.error(...args),
  level: 3,
};

async function upload(origins) {
  const env = { ...loadEnv('production', APP_DIR, 'VITE_'), ...process.env };
  const apiKey = env.VITE_BUGSNAG_API_KEY;
  if (env.VITE_BUGSNAG_ENABLED !== 'true' || !apiKey) {
    console.log('Bugsnag reporting is off or has no key; not uploading maps.');
    return;
  }
  const { version } = JSON.parse(
    await readFile(path.join(APP_DIR, 'package.json'), 'utf8')
  );
  const appVersion = env.VITE_APP_VERSION || version;
  for (const baseUrl of origins) {
    try {
      await browser.uploadMultiple({
        apiKey,
        baseUrl,
        directory: DIST,
        appVersion,
        overwrite: true,
        projectRoot: APP_DIR,
        logger,
        ...(env.BUGSNAG_SOURCE_MAP_ENDPOINT
          ? { endpoint: env.BUGSNAG_SOURCE_MAP_ENDPOINT }
          : {}),
      });
      console.log(`Uploaded source maps for ${baseUrl} (${appVersion}).`);
    } catch (error) {
      console.warn(
        `Could not upload source maps for ${baseUrl}; stack traces from this build stay minified.`,
        error?.message || error
      );
    }
  }
}

const maps = await mapFiles(DIST);
if (!maps.length) {
  console.log('No source maps in dist.');
} else {
  await upload(baseUrls(process.argv.slice(2)));
  await Promise.all(maps.map((file) => rm(file)));
  console.log(`Removed ${maps.length} source maps from dist.`);
}
