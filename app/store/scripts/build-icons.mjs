// Builds every app icon, splash screen, and store icon from one vector source:
// the gold Jerusalem cross of the 2019 Book of Common Prayer on oxblood leather.
//
//   node store/scripts/build-icons.mjs        (run from app/)
//
// Writes the iOS asset catalogs, Android mipmaps/splashes, the
// @capacitor/assets sources in assets/, and store icons in store/icons/.
// Uses sharp (installed with @capacitor/assets).
import {
  mkdirSync,
  rmSync,
  writeFileSync,
  readdirSync,
  existsSync,
} from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const APP = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const STORE = join(APP, 'store');
const IOS_ASSETS = join(APP, 'ios/App/App/Assets.xcassets');
const ANDROID_RES = join(APP, 'android/app/src/main/res');
const GRAIN = join(STORE, 'source/leather-grain.png');

// Brand colors: the liturgical red of the app (--accent-default) and gilt.
export const RED = '#8c1d22';
export const RED_DEEP = '#4f0c10';
export const RED_LIGHT = '#a8282c';
export const INK = '#161513';

// The cross, on a 200-unit square centered on the origin. A cross potent
// (bars ending in crossbars) with a Greek cross in each quarter.
function plus(cx, cy, half, arm) {
  return `M ${cx - arm} ${cy - half} h ${2 * arm} v ${half - arm} h ${half - arm} v ${2 * arm} h ${-(half - arm)} v ${half - arm} h ${-2 * arm} v ${-(half - arm)} h ${-(half - arm)} v ${-2 * arm} h ${half - arm} Z`;
}
const BAR = 8.5; // half-width of the great cross's arms
const END = 88; // reach of the potent crossbars
const POT = 23; // half-length of each potent crossbar
const POT_W = 12; // thickness of each potent crossbar
const S = END - POT_W;
export const CROSS_PATH = [
  `M ${-BAR} ${-S} H ${-POT} V ${-END} H ${POT} V ${-S} H ${BAR} V ${-BAR} H ${S} V ${-POT} H ${END} V ${POT} H ${S} V ${BAR} H ${BAR} V ${S} H ${POT} V ${END} H ${-POT} V ${S} H ${-BAR} V ${BAR} H ${-S} V ${POT} H ${-END} V ${-POT} H ${-S} V ${-BAR} H ${-BAR} Z`,
  plus(-47, -47, 25, 4.75),
  plus(47, -47, 25, 4.75),
  plus(-47, 47, 25, 4.75),
  plus(47, 47, 25, 4.75),
].join(' ');

// Gilt stamped into leather: a dark impression below, a catch-light above,
// and a warm gold gradient on the face.
export function giltCross({ scale = 1, flat = false, fill } = {}) {
  const t = `scale(${scale})`;
  if (fill) return `<path transform="${t}" d="${CROSS_PATH}" fill="${fill}"/>`;
  return `
    <defs>
      <linearGradient id="gold" x1="-90" y1="-90" x2="90" y2="90" gradientUnits="userSpaceOnUse">
        <stop offset="0" stop-color="#fbeec4"/>
        <stop offset="0.38" stop-color="#e3c47e"/>
        <stop offset="0.7" stop-color="#c79f55"/>
        <stop offset="1" stop-color="#a87c3c"/>
      </linearGradient>
      <filter id="impress" x="-20%" y="-20%" width="140%" height="140%">
        <feGaussianBlur stdDeviation="1.6"/>
      </filter>
    </defs>
    ${
      flat
        ? ''
        : `<path transform="${t} translate(1.1 1.9)" d="${CROSS_PATH}" fill="#1e0504" opacity="0.55" filter="url(#impress)"/>
    <path transform="${t} translate(-0.7 -0.7)" d="${CROSS_PATH}" fill="#fff6d8" opacity="0.55"/>`
    }
    <path transform="${t}" d="${CROSS_PATH}" fill="url(#gold)"/>
    <path transform="${t}" d="${CROSS_PATH}" fill="none" stroke="#7a5524" stroke-opacity="0.35" stroke-width="0.6"/>`;
}

export function svg(size, body, viewBox = '-100 -100 200 200') {
  return Buffer.from(
    `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="${viewBox}">${body}</svg>`
  );
}

function leatherBody(base = RED, deep = RED_DEEP, light = RED_LIGHT) {
  return `
    <defs>
      <radialGradient id="hide" cx="0" cy="-35" r="150" gradientUnits="userSpaceOnUse">
        <stop offset="0" stop-color="${light}"/>
        <stop offset="0.55" stop-color="${base}"/>
        <stop offset="1" stop-color="${deep}"/>
      </radialGradient>
    </defs>
    <rect x="-100" y="-100" width="200" height="200" fill="url(#hide)"/>`;
}

// Leather background (opaque square), optionally a dark-mode hide.
export async function leather(size, { dark = false } = {}) {
  const body = dark
    ? leatherBody('#2a1513', '#0d0605', '#3b1d19')
    : leatherBody();
  // Soften the grain toward mid-gray so it reads as texture, not noise.
  const grain = await sharp(GRAIN)
    .resize(size, size)
    .toColourspace('b-w')
    .linear(0.45, 128 * 0.55)
    .toBuffer();
  return sharp(svg(size, body))
    .composite([{ input: grain, blend: 'soft-light' }])
    .flatten({ background: dark ? INK : RED })
    .png()
    .toBuffer();
}

// The cross alone on transparent, at `fraction` of the canvas.
async function cross(size, fraction, opts = {}) {
  return sharp(svg(size, giltCross({ scale: fraction, ...opts })))
    .png()
    .toBuffer();
}

async function composite(size, background, fraction, crossOpts = {}) {
  const fg = await cross(size, fraction, crossOpts);
  return sharp(background)
    .composite([{ input: fg }])
    .png()
    .toBuffer();
}

async function write(
  path,
  buffer,
  { size, alpha = true, format = 'png' } = {}
) {
  mkdirSync(dirname(path), { recursive: true });
  let img = sharp(buffer);
  if (size) img = img.resize(size[0], size[1] ?? size[0], { fit: 'cover' });
  if (!alpha) img = img.flatten({ background: RED }).removeAlpha();
  if (format === 'jpeg')
    img = img.jpeg({ quality: 92, chromaSubsampling: '4:4:4' });
  else img = img.png({ compressionLevel: 9 });
  await img.toFile(path);
}

// iOS draws the icon full-bleed under a rounded mask; the cross fills ~64%.
const IOS_CROSS = 0.64;
// Android adaptive icons are 108dp with a 66dp safe circle; keep the cross's
// farthest corner inside it.
const ADAPTIVE_CROSS = 0.56;

async function main() {
  const master = await leather(2048);
  const masterDark = await leather(2048, { dark: true });
  const iconLight = await composite(2048, master, IOS_CROSS);
  const iconDark = await composite(2048, masterDark, IOS_CROSS);

  // --- iOS: single-size app icon with dark and tinted appearances (Xcode 14+).
  const appIcon = join(IOS_ASSETS, 'AppIcon.appiconset');
  rmSync(appIcon, { recursive: true, force: true });
  await write(join(appIcon, 'AppIcon-1024.png'), iconLight, {
    size: [1024],
    alpha: false,
  });
  await write(join(appIcon, 'AppIcon-1024-dark.png'), iconDark, {
    size: [1024],
    alpha: false,
  });
  const tinted = await sharp(
    svg(
      2048,
      `<rect x="-100" y="-100" width="200" height="200" fill="#000"/>${giltCross({ scale: IOS_CROSS, fill: '#fff' })}`
    )
  )
    .png()
    .toBuffer();
  await write(join(appIcon, 'AppIcon-1024-tinted.png'), tinted, {
    size: [1024],
  });
  writeFileSync(
    join(appIcon, 'Contents.json'),
    JSON.stringify(
      {
        images: [
          {
            filename: 'AppIcon-1024.png',
            idiom: 'universal',
            platform: 'ios',
            size: '1024x1024',
          },
          {
            appearances: [{ appearance: 'luminosity', value: 'dark' }],
            filename: 'AppIcon-1024-dark.png',
            idiom: 'universal',
            platform: 'ios',
            size: '1024x1024',
          },
          {
            appearances: [{ appearance: 'luminosity', value: 'tinted' }],
            filename: 'AppIcon-1024-tinted.png',
            idiom: 'universal',
            platform: 'ios',
            size: '1024x1024',
          },
        ],
        info: { author: 'xcode', version: 1 },
      },
      null,
      2
    ) + '\n'
  );

  // --- iOS launch screen: the book cover, centered and cropped to fill.
  const splashSet = join(IOS_ASSETS, 'Splash.imageset');
  rmSync(join(IOS_ASSETS, 'LaunchImage.imageset'), {
    recursive: true,
    force: true,
  });
  rmSync(splashSet, { recursive: true, force: true });
  const splash = await composite(2732, await leather(2732), 0.22);
  for (const [scale, px] of [
    ['1x', 1366],
    ['2x', 2732],
    ['3x', 2732],
  ]) {
    // JPEG: the grain makes a 2732px PNG several megabytes.
    await write(join(splashSet, `splash-${scale}.jpg`), splash, {
      size: [px],
      alpha: false,
      format: 'jpeg',
    });
  }
  writeFileSync(
    join(splashSet, 'Contents.json'),
    JSON.stringify(
      {
        images: ['1x', '2x', '3x'].map((scale) => ({
          filename: `splash-${scale}.jpg`,
          idiom: 'universal',
          scale,
        })),
        info: { author: 'xcode', version: 1 },
      },
      null,
      2
    ) + '\n'
  );

  // --- Android launcher icons.
  const densities = {
    ldpi: 0.75,
    mdpi: 1,
    hdpi: 1.5,
    xhdpi: 2,
    xxhdpi: 3,
    xxxhdpi: 4,
  };
  const adaptiveFg = await cross(2048, ADAPTIVE_CROSS);
  const legacy = await composite(2048, master, 0.58);
  const roundMask = svg(2048, '<circle cx="0" cy="0" r="100" fill="#fff"/>');
  const legacyRound = await sharp(legacy)
    .composite([{ input: roundMask, blend: 'dest-in' }])
    .png()
    .toBuffer();
  for (const [name, factor] of Object.entries(densities)) {
    const dir = join(ANDROID_RES, `mipmap-${name}`);
    const legacyPx = Math.round(48 * factor);
    const adaptivePx = Math.round(108 * factor);
    await write(join(dir, 'ic_launcher.png'), legacy, { size: [legacyPx] });
    await write(join(dir, 'ic_launcher_round.png'), legacyRound, {
      size: [legacyPx],
    });
    await write(join(dir, 'ic_launcher_foreground.png'), adaptiveFg, {
      size: [adaptivePx],
    });
    await write(join(dir, 'ic_launcher_background.png'), master, {
      size: [adaptivePx],
      alpha: false,
    });
  }
  const adaptiveXml = `<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@mipmap/ic_launcher_background" />
    <foreground android:drawable="@mipmap/ic_launcher_foreground" />
    <monochrome android:drawable="@drawable/ic_launcher_monochrome" />
</adaptive-icon>
`;
  writeFileSync(
    join(ANDROID_RES, 'mipmap-anydpi-v26/ic_launcher.xml'),
    adaptiveXml
  );
  writeFileSync(
    join(ANDROID_RES, 'mipmap-anydpi-v26/ic_launcher_round.xml'),
    adaptiveXml
  );
  // Themed (Material You) icon: the cross as a vector, inside the safe zone.
  const k = ADAPTIVE_CROSS * (108 / 200);
  writeFileSync(
    join(ANDROID_RES, 'drawable/ic_launcher_monochrome.xml'),
    `<?xml version="1.0" encoding="utf-8"?>
<!-- Generated by store/scripts/build-icons.mjs: the Jerusalem cross for themed icons. -->
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <group android:translateX="54" android:translateY="54" android:scaleX="${k.toFixed(4)}" android:scaleY="${k.toFixed(4)}">
        <path android:fillColor="#FFFFFFFF" android:pathData="${CROSS_PATH}" />
    </group>
</vector>
`
  );
  // Remove the template's unused vector placeholders.
  rmSync(join(ANDROID_RES, 'drawable-v24/ic_launcher_foreground.xml'), {
    force: true,
  });
  rmSync(join(ANDROID_RES, 'drawable/ic_launcher_background.xml'), {
    force: true,
  });
  if (
    existsSync(join(ANDROID_RES, 'drawable-v24')) &&
    readdirSync(join(ANDROID_RES, 'drawable-v24')).length === 0
  ) {
    rmSync(join(ANDROID_RES, 'drawable-v24'), { recursive: true });
  }

  // Android 12+ splash: the cross on the leather color (see styles.xml).
  // 288dp canvas; the icon must sit inside its 192dp circle.
  const splashIcon = await cross(2048, 0.6);
  for (const [name, factor] of Object.entries(densities)) {
    await write(
      join(
        ANDROID_RES,
        `drawable-${name === 'ldpi' ? 'ldpi' : name}/splash_icon.png`
      ),
      splashIcon,
      {
        size: [Math.round(288 * factor)],
      }
    );
  }
  // Android 7–11 splash: full-screen cover art at every existing size.
  const tallSplash = async (w, h) => {
    const side = Math.max(w, h);
    const bg = await leather(side);
    const art = await composite(side, bg, (0.32 * Math.min(w, h)) / side);
    return sharp(art).resize(w, h, { fit: 'cover' }).png().toBuffer();
  };
  const splashSizes = {
    drawable: [320, 480],
    'drawable-port-ldpi': [240, 320],
    'drawable-port-mdpi': [320, 480],
    'drawable-port-hdpi': [480, 800],
    'drawable-port-xhdpi': [720, 1280],
    'drawable-port-xxhdpi': [960, 1600],
    'drawable-port-xxxhdpi': [1280, 1920],
    'drawable-land-ldpi': [320, 240],
    'drawable-land-mdpi': [480, 320],
    'drawable-land-hdpi': [800, 480],
    'drawable-land-xhdpi': [1280, 720],
    'drawable-land-xxhdpi': [1600, 960],
    'drawable-land-xxxhdpi': [1920, 1280],
  };
  // WebP keeps the leather grain without megabytes of PNG noise.
  for (const [dir, [w, h]] of Object.entries(splashSizes)) {
    rmSync(join(ANDROID_RES, dir, 'splash.png'), { force: true });
    await sharp(await tallSplash(w, h))
      .removeAlpha()
      .webp({ quality: 82 })
      .toFile(join(ANDROID_RES, dir, 'splash.webp'));
  }

  // --- @capacitor/assets sources, kept in step with the generated art.
  await write(join(APP, 'assets/icon-only.png'), iconLight, {
    size: [1024],
    alpha: false,
  });
  await write(join(APP, 'assets/icon-foreground.png'), adaptiveFg, {
    size: [1024],
  });
  await write(join(APP, 'assets/icon-background.png'), master, {
    size: [1024],
    alpha: false,
  });
  await write(join(APP, 'assets/splash.jpg'), splash, {
    alpha: false,
    format: 'jpeg',
  });
  await write(
    join(APP, 'assets/splash-dark.jpg'),
    await composite(2732, await leather(2732, { dark: true }), 0.22),
    { alpha: false, format: 'jpeg' }
  );
  rmSync(join(APP, 'assets/icon-only512.png'), { force: true });
  rmSync(join(APP, 'assets/splash.png'), { force: true });
  rmSync(join(APP, 'assets/splash-dark.png'), { force: true });

  // --- Store icons.
  const icons = join(STORE, 'icons');
  rmSync(icons, { recursive: true, force: true });
  await write(join(icons, 'app-store-icon-1024.png'), iconLight, {
    size: [1024],
    alpha: false,
  });
  await write(join(icons, 'app-store-icon-1024-dark.png'), iconDark, {
    size: [1024],
    alpha: false,
  });
  await write(join(icons, 'app-store-icon-1024-tinted.png'), tinted, {
    size: [1024],
  });
  await write(join(icons, 'google-play-icon-512.png'), iconLight, {
    size: [512],
  });
  // Layers for Icon Composer (Liquid Glass): background and foreground, 1024.
  await write(join(icons, 'icon-composer/background.png'), master, {
    size: [1024],
    alpha: false,
  });
  await write(
    join(icons, 'icon-composer/cross.png'),
    await cross(2048, IOS_CROSS),
    { size: [1024] }
  );
  writeFileSync(
    join(icons, 'icon-composer/cross.svg'),
    svg(1024, giltCross({ scale: IOS_CROSS, fill: '#e3c47e' }))
  );
  // Vector master, for print, web, and future art.
  writeFileSync(
    join(icons, 'jerusalem-cross.svg'),
    svg(1024, giltCross({ fill: '#000' }))
  );
  // Sizes commonly asked for elsewhere (social, web, press kits).
  for (const px of [1024, 512, 256, 192, 180, 152, 120, 64, 48, 32]) {
    await write(join(icons, `sizes/icon-${px}.png`), iconLight, {
      size: [px],
      alpha: false,
    });
  }
  console.log('Icons and splash screens written.');
}

if (process.argv[1] === fileURLToPath(import.meta.url)) await main();
