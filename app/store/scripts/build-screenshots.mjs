// Builds the App Store and Google Play screenshot sets, the Play feature
// graphic, and social images from real captures in store/screenshots/raw/.
//
//   node store/scripts/build-screenshots.mjs        (run from app/)
//
// Each slide is a caption over the capture on the prayer-book leather,
// rendered at every size the stores ask for with headless Google Chrome
// (set CHROME to override its path) in Adobe Caslon Pro.
import { execFileSync } from 'node:child_process';
import {
  existsSync,
  mkdirSync,
  mkdtempSync,
  rmSync,
  writeFileSync,
} from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import sharp from 'sharp';
import { leather, giltCross, svg } from './build-icons.mjs';

const APP = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const STORE = join(APP, 'store');
const RAW = join(STORE, 'screenshots/raw');
const CHROME =
  process.env.CHROME ||
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

// Order matters: the first three are what most people see in search results.
// Google Play shows up to eight, so it takes the first eight.
export const SLIDES = [
  {
    slug: 'office',
    eyebrow: 'The Daily Office',
    title: 'Pray with the Church, wherever you are',
    sub: 'Morning, Midday, Evening, and Compline from the 2019 Book of Common Prayer',
  },
  {
    slug: 'audio',
    eyebrow: 'Listen',
    title: 'Pray along with audio',
    sub: 'Every office read aloud, word by word, even with your screen locked',
  },
  {
    slug: 'book',
    eyebrow: 'Book view',
    title: 'Turn the pages like a prayer book',
    sub: 'A quiet, page-by-page way to pray, with nothing else on the screen',
  },
  {
    slug: 'psalm',
    eyebrow: 'Everything in order',
    title: 'Psalms, lessons, and prayers, all in one place',
    sub: 'No ribbons to set, no lectionary to look up, no rubrics to decode',
  },
  {
    slug: 'calendar',
    eyebrow: 'The Christian year',
    title: 'Keep the feasts and seasons',
    sub: 'Holy days, fasts, and commemorations in their liturgical colors',
  },
  {
    slug: 'display',
    eyebrow: 'Make it yours',
    title: 'Easy on the eyes',
    sub: 'Light, sepia, or dark; six typefaces; any text size',
  },
  {
    slug: 'settings',
    eyebrow: 'As the rubrics allow',
    title: 'Pray the office your way',
    sub: 'Choose the psalter cycle, lectionary, translation, canticles, and more',
  },
  {
    slug: 'saints',
    eyebrow: 'The saints',
    title: 'Meet the saints of the day',
    sub: 'Lives, traditions, and further reading for each commemoration',
  },
  {
    slug: 'dark',
    eyebrow: 'Night prayer',
    title: 'A dark page for Compline',
    sub: 'Follows your device, or choose a theme of your own',
  },
  {
    slug: 'podcasts',
    eyebrow: 'Podcasts',
    title: 'The offices in your podcast app',
    sub: 'Morning and Evening Prayer and the daily readings, new every day',
  },
];

// Every size the stores accept. `raw` names the capture set to frame;
// `scale` sizes the caption relative to the canvas width.
const IPHONE = {
  raw: 'iphone',
  device: 0.8,
  scale: 1,
  radius: 0.105,
  bezel: 0.014,
};
const IPAD = {
  raw: 'ipad',
  device: 0.78,
  scale: 0.7,
  radius: 0.035,
  bezel: 0.01,
};
export const TARGETS = [
  { dir: 'screenshots/ios/iphone-6.9', w: 1320, h: 2868, ...IPHONE }, // iPhone 18/17/16 Pro Max, Air
  { dir: 'screenshots/ios/iphone-6.3', w: 1206, h: 2622, ...IPHONE }, // iPhone 18/17/16 Pro (required)
  { dir: 'screenshots/ios/iphone-6.5', w: 1284, h: 2778, ...IPHONE }, // iPhone 11 Pro Max – 14 Plus
  { dir: 'screenshots/ios/iphone-6.1', w: 1170, h: 2532, ...IPHONE }, // iPhone 12–14
  { dir: 'screenshots/ios/iphone-5.5', w: 1242, h: 2208, ...IPHONE, device: 0.72 }, // Home-button iPhones
  { dir: 'screenshots/ios/ipad-13', w: 2064, h: 2752, ...IPAD }, // iPad Pro 13", iPad Air 13" (required)
  { dir: 'screenshots/ios/ipad-12.9', w: 2048, h: 2732, ...IPAD }, // iPad Pro 12.9"
  { dir: 'screenshots/ios/ipad-11', w: 1668, h: 2388, ...IPAD }, // iPad Pro 11", iPad Air 11"
  {
    dir: 'metadata/android/en-US/images/phoneScreenshots',
    w: 1080,
    h: 1920,
    raw: 'android-phone',
    device: 0.7,
    scale: 1,
    radius: 0.06,
    bezel: 0.014,
    max: 8,
  },
  {
    dir: 'metadata/android/en-US/images/sevenInchScreenshots',
    w: 1080,
    h: 1920,
    raw: 'android-tablet7',
    device: 0.74,
    scale: 0.85,
    radius: 0.035,
    bezel: 0.012,
    max: 8,
  },
  {
    dir: 'metadata/android/en-US/images/tenInchScreenshots',
    w: 1440,
    h: 2560,
    raw: 'android-tablet10',
    device: 0.74,
    scale: 0.85,
    radius: 0.03,
    bezel: 0.01,
    max: 8,
  },
];

function rawPath(set, slug) {
  for (const ext of ['png', 'jpg']) {
    const p = join(RAW, set, `${slug}.${ext}`);
    if (existsSync(p)) return p;
  }
  return null;
}

const FONT_STACK = `'Adobe Caslon Pro', 'Big Caslon', 'Libre Caslon Text', Georgia, serif`;

function slideHtml(t, slide, capture, background) {
  const { w, h } = t;
  const u = w / 100; // 1vw in px, so the layout scales with the canvas
  const s = t.scale;
  const deviceW = w * t.device;
  // Every slide in a set puts the device at the same height; the caption
  // centers in the space above it.
  const top = (t.top ?? 56) * u * s;
  return `<!doctype html><html><head><meta charset="utf-8"><style>
    html, body { margin: 0; width: ${w}px; height: ${h}px; overflow: hidden; }
    body {
      background: url('${background}') center / cover;
      font-family: ${FONT_STACK};
      color: #fbf3e2;
      text-align: center;
      -webkit-font-smoothing: antialiased;
    }
    .caption {
      height: ${top - 3 * u * s}px;
      padding: ${2 * u * s}px ${8 * u}px 0;
      box-sizing: border-box;
      display: flex;
      flex-direction: column;
      justify-content: center;
    }
    .eyebrow {
      font-variant-caps: all-small-caps;
      letter-spacing: 0.16em;
      font-size: ${5.2 * u * s}px;
      color: #e8cf8f;
      margin: 0 0 ${1.6 * u * s}px;
    }
    .rule { width: ${10 * u * s}px; height: ${0.25 * u * s}px; background: #c9a45a; margin: 0 auto ${2.6 * u * s}px; opacity: 0.8; }
    h1 {
      font-weight: 400;
      font-size: ${8.4 * u * s}px;
      line-height: 1.08;
      margin: 0 auto;
      max-width: ${84 * u}px;
      text-wrap: balance;
      letter-spacing: -0.005em;
    }
    p.sub {
      font-style: italic;
      font-size: ${4.3 * u * s}px;
      line-height: 1.3;
      margin: ${2.4 * u * s}px auto 0;
      max-width: ${80 * u}px;
      color: #f3e4c8;
      text-wrap: balance;
    }
    .device {
      position: absolute;
      left: ${(w - deviceW) / 2}px;
      top: ${top}px;
      width: ${deviceW}px;
      padding: ${w * t.bezel}px;
      box-sizing: border-box;
      background: #15100e;
      border-radius: ${w * t.radius}px;
      box-shadow: 0 ${3 * u}px ${8 * u}px rgb(20 2 2 / 0.55), 0 0 0 ${0.18 * u}px rgb(255 235 200 / 0.18);
    }
    .device img { display: block; width: 100%; border-radius: ${w * (t.radius - t.bezel)}px; }
  </style></head><body>
    <div class="caption">
      <p class="eyebrow">${slide.eyebrow}</p>
      <div class="rule"></div>
      <h1>${slide.title}</h1>
      <p class="sub">${slide.sub}</p>
    </div>
    <div class="device"><img src="${capture}"></div>
  </body></html>`;
}

function render(htmlPath, out, w, h) {
  execFileSync(
    CHROME,
    [
      '--headless=new',
      '--disable-gpu',
      '--hide-scrollbars',
      '--force-device-scale-factor=1',
      '--allow-file-access-from-files',
      '--virtual-time-budget=3000',
      `--window-size=${w},${h}`,
      `--screenshot=${out}`,
      pathToFileURL(htmlPath).href,
    ],
    { stdio: 'ignore' }
  );
}

async function toJpeg(png, out, w, h) {
  mkdirSync(dirname(out), { recursive: true });
  await sharp(png)
    .resize(w, h, { fit: 'cover', position: 'top' })
    .flatten({ background: '#8c1d22' })
    .jpeg({ quality: 90, chromaSubsampling: '4:4:4', mozjpeg: true })
    .toFile(out);
}

async function main() {
  const work = mkdtempSync(join(tmpdir(), 'do-shots-'));
  const only = process.argv[2];
  try {
    for (const t of TARGETS) {
      if (only && !t.dir.includes(only)) continue;
      const outDir = join(STORE, t.dir);
      rmSync(outDir, { recursive: true, force: true });
      mkdirSync(outDir, { recursive: true });
      const bg = join(work, `bg-${t.w}x${t.h}.png`);
      const side = Math.max(t.w, t.h);
      await sharp(await leather(side))
        .resize(t.w, t.h, { fit: 'cover' })
        .png()
        .toFile(bg);
      let n = 0;
      for (const slide of SLIDES) {
        if (t.max && n >= t.max) break;
        const capture = rawPath(t.raw, slide.slug);
        if (!capture) continue;
        n += 1;
        const html = join(work, 'slide.html');
        writeFileSync(
          html,
          slideHtml(
            t,
            slide,
            pathToFileURL(capture).href,
            pathToFileURL(bg).href
          )
        );
        const png = join(work, 'slide.png');
        render(html, png, t.w, t.h);
        await toJpeg(
          png,
          join(outDir, `${String(n).padStart(2, '0')}-${slide.slug}.jpg`),
          t.w,
          t.h
        );
      }
      console.log(`${t.dir}: ${n} screenshots`);
    }
    if (!only || only === 'graphics') await graphics(work);
  } finally {
    rmSync(work, { recursive: true, force: true });
  }
}

// Google Play feature graphic (1024x500) and social/press images.
async function graphics(work) {
  const hero = rawPath('iphone', 'office');
  const make = async (out, w, h, { phone = true } = {}) => {
    const bg = join(work, `bg-g-${w}.png`);
    await sharp(await leather(Math.max(w, h)))
      .resize(w, h, { fit: 'cover' })
      .png()
      .toFile(bg);
    const cross = join(work, 'cross.svg');
    writeFileSync(cross, svg(400, giltCross({ scale: 0.95 })));
    const u = h / 100;
    // Leave room for the phone on the right.
    const k = phone ? 0.84 : 1;
    const html = `<!doctype html><html><head><meta charset="utf-8"><style>
      html, body { margin: 0; width: ${w}px; height: ${h}px; overflow: hidden; }
      body { background: url('${pathToFileURL(bg).href}') center / cover; font-family: ${FONT_STACK}; color: #fbf3e2; -webkit-font-smoothing: antialiased; }
      .wrap { position: absolute; left: ${phone ? 7 * u : 0}px; right: ${phone ? 'auto' : 0}px; top: 0; bottom: 0; display: flex; align-items: center; gap: ${5 * u}px; ${phone ? '' : 'justify-content: center;'} }
      .cross { width: ${k * 30 * u}px; height: ${k * 30 * u}px; }
      .eyebrow { font-variant-caps: all-small-caps; letter-spacing: 0.16em; font-size: ${k * 5.6 * u}px; color: #e8cf8f; margin: 0 0 ${1.5 * u}px; }
      h1 { font-weight: 400; font-size: ${k * 14 * u}px; line-height: 1; margin: 0; white-space: nowrap; }
      p { font-style: italic; font-size: ${k * 6.4 * u}px; margin: ${2.8 * u}px 0 0; color: #f3e4c8; }
      .phone { position: absolute; right: ${7 * u}px; top: ${14 * u}px; width: ${44 * u}px; padding: ${0.9 * u}px; background: #15100e; border-radius: ${6 * u}px; box-shadow: 0 ${2 * u}px ${6 * u}px rgb(20 2 2 / 0.6); }
      .phone img { display: block; width: 100%; border-radius: ${5.2 * u}px; }
    </style></head><body>
      <div class="wrap">
        <img class="cross" src="${pathToFileURL(cross).href}">
        <div>
          <p class="eyebrow">Morning · Midday · Evening · Compline</p>
          <h1>The Daily Office</h1>
          <p>The Book of Common Prayer (2019)</p>
        </div>
      </div>
      ${phone && hero ? `<div class="phone"><img src="${pathToFileURL(hero).href}"></div>` : ''}
    </body></html>`;
    const htmlPath = join(work, 'graphic.html');
    writeFileSync(htmlPath, html);
    const png = join(work, 'graphic.png');
    render(htmlPath, png, w, h);
    mkdirSync(dirname(out), { recursive: true });
    const img = sharp(png).resize(w, h).flatten({ background: '#8c1d22' });
    if (out.endsWith('.png')) await img.png().toFile(out);
    else
      await img
        .jpeg({ quality: 92, chromaSubsampling: '4:4:4', mozjpeg: true })
        .toFile(out);
  };
  const images = join(STORE, 'metadata/android/en-US/images');
  await make(join(images, 'featureGraphic.png'), 1024, 500);
  await sharp(join(STORE, 'icons/google-play-icon-512.png')).toFile(
    join(images, 'icon.png')
  );
  await make(join(STORE, 'graphics/social-1200x630.jpg'), 1200, 630);
  await make(join(STORE, 'graphics/twitter-1600x900.jpg'), 1600, 900);
  await make(join(STORE, 'graphics/banner-1500x500.jpg'), 1500, 500, {
    phone: false,
  });
  await make(join(STORE, 'graphics/square-1080.jpg'), 1080, 1080, {
    phone: false,
  });
  console.log('Feature graphic and social images written.');
}

if (process.argv[1] === fileURLToPath(import.meta.url)) await main();
