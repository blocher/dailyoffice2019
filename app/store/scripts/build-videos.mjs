// Builds the App Store app previews and a landscape promo video (for the
// Google Play YouTube slot and social media) from simulator recordings.
//
//   node store/scripts/build-videos.mjs        (run from app/)
//
// Inputs, recorded with `xcrun simctl io <device> recordVideo` while the app
// runs the store tour (see RELEASE_GUIDE.md):
//   store/video/raw/iphone.mp4   iPhone 6.9" (1320x2868)
//   store/video/raw/ipad.mp4     iPad 13" (2064x2752)
// Outputs go to store/video/ (ignored by git; upload them by hand).
// Needs ffmpeg and Google Chrome (for the caption cards).
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import sharp from 'sharp';
import { leather, giltCross, svg } from './build-icons.mjs';

const APP = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const VIDEO = join(APP, 'store/video');
const CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const FONT = `'Adobe Caslon Pro', 'Big Caslon', Georgia, serif`;

// Apple's app preview spec: H.264 at ~10 Mbps, 30 fps, stereo AAC.
const PREVIEW_ENCODE = [
  '-c:v', 'libx264', '-profile:v', 'high', '-level', '4.0', '-preset', 'slow',
  '-b:v', '10M', '-minrate', '10M', '-maxrate', '10M', '-bufsize', '10M', '-x264-params', 'nal-hrd=cbr',
  '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart',
];
const SILENCE = ['-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=48000'];

// Captions for the promo, timed to the store tour.
const CAPTIONS = [
  { from: 0, to: 4, eyebrow: 'The Daily Office', title: 'Pray with the Church, wherever you are' },
  { from: 4, to: 9, eyebrow: 'Everything in order', title: 'Psalms, lessons, and prayers on one page' },
  { from: 9, to: 15.6, eyebrow: 'Listen', title: 'Pray along with audio, word by word' },
  { from: 15.6, to: 30, eyebrow: 'Book view', title: 'Turn the pages like a prayer book' },
];

function ffmpeg(args) {
  execFileSync('ffmpeg', ['-v', 'error', '-y', ...args], { stdio: 'inherit' });
}

function chrome(html, out, w, h, work) {
  const file = join(work, `card-${Math.random().toString(36).slice(2)}.html`);
  writeFileSync(file, html);
  execFileSync(
    CHROME,
    [
      '--headless=new',
      '--disable-gpu',
      '--hide-scrollbars',
      '--force-device-scale-factor=1',
      '--default-background-color=00000000',
      '--allow-file-access-from-files',
      '--virtual-time-budget=2000',
      `--window-size=${w},${h}`,
      `--screenshot=${out}`,
      pathToFileURL(file).href,
    ],
    { stdio: 'ignore' }
  );
}

function captionHtml({ eyebrow, title }) {
  return `<!doctype html><html><head><meta charset="utf-8"><style>
    html, body { margin: 0; width: 1920px; height: 1080px; background: transparent; }
    .c { position: absolute; left: 150px; width: 900px; top: 50%; transform: translateY(-50%);
      font-family: ${FONT}; color: #fbf3e2; -webkit-font-smoothing: antialiased; }
    .e { font-variant-caps: all-small-caps; letter-spacing: 0.16em; font-size: 46px; color: #e8cf8f; margin: 0 0 18px; }
    .r { width: 90px; height: 3px; background: #c9a45a; margin: 0 0 34px; }
    h1 { font-weight: 400; font-size: 104px; line-height: 1.06; margin: 0; text-wrap: balance; }
  </style></head><body><div class="c"><p class="e">${eyebrow}</p><div class="r"></div><h1>${title}</h1></div></body></html>`;
}

function endCardHtml(cross) {
  return `<!doctype html><html><head><meta charset="utf-8"><style>
    html, body { margin: 0; width: 1920px; height: 1080px; background: transparent; }
    .c { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center;
      font-family: ${FONT}; color: #fbf3e2; text-align: center; -webkit-font-smoothing: antialiased; }
    img { width: 260px; height: 260px; margin-bottom: 40px; }
    h1 { font-weight: 400; font-size: 130px; margin: 0; line-height: 1; }
    p { font-style: italic; font-size: 52px; margin: 26px 0 0; color: #f3e4c8; }
    .e { font-style: normal; font-variant-caps: all-small-caps; letter-spacing: 0.16em; font-size: 44px; color: #e8cf8f; margin-top: 56px; }
  </style></head><body><div class="c">
    <img src="${pathToFileURL(cross).href}">
    <h1>The Daily Office</h1>
    <p>The Book of Common Prayer (2019)</p>
    <p class="e">Free on the App Store and Google Play</p>
  </div></body></html>`;
}

async function previews() {
  const iphone = join(VIDEO, 'raw/iphone.mp4');
  const ipad = join(VIDEO, 'raw/ipad.mp4');
  if (existsSync(iphone)) {
    ffmpeg([
      '-i', iphone, ...SILENCE,
      '-filter_complex', '[0:v]fps=30,scale=886:-2:flags=lanczos,crop=886:1920:0:(ih-1920)/2,format=yuv420p[v]',
      '-map', '[v]', '-map', '1:a', '-shortest', ...PREVIEW_ENCODE,
      join(VIDEO, 'app-preview-iphone-886x1920.mp4'),
    ]);
  }
  if (existsSync(ipad)) {
    ffmpeg([
      '-i', ipad, ...SILENCE,
      '-filter_complex', '[0:v]fps=30,scale=1200:1600:flags=lanczos,format=yuv420p[v]',
      '-map', '[v]', '-map', '1:a', '-shortest', ...PREVIEW_ENCODE,
      join(VIDEO, 'app-preview-ipad-1200x1600.mp4'),
    ]);
  }
}

async function promo() {
  const iphone = join(VIDEO, 'raw/iphone.mp4');
  if (!existsSync(iphone)) return;
  const work = mkdtempSync(join(tmpdir(), 'do-promo-'));
  try {
    // Background, the phone's bezel, and a rounded mask for the screen.
    const bg = join(work, 'bg.png');
    await sharp(await leather(1920)).resize(1920, 1080, { fit: 'cover' }).png().toFile(bg);
    const phoneH = 960;
    const phoneW = Math.round((phoneH * 1320) / 2868 / 2) * 2;
    const bezel = 14;
    const r = 62;
    const frame = join(work, 'frame.png');
    await sharp(
      Buffer.from(
        `<svg xmlns="http://www.w3.org/2000/svg" width="${phoneW + 2 * bezel}" height="${phoneH + 2 * bezel}"><rect width="100%" height="100%" rx="${r + bezel}" fill="#15100e"/></svg>`
      )
    )
      .png()
      .toFile(frame);
    const mask = join(work, 'mask.png');
    await sharp(
      Buffer.from(
        `<svg xmlns="http://www.w3.org/2000/svg" width="${phoneW}" height="${phoneH}"><rect width="100%" height="100%" rx="${r}" fill="#fff"/></svg>`
      )
    )
      .png()
      .toFile(mask);
    const captions = CAPTIONS.map((c, i) => {
      const out = join(work, `caption-${i}.png`);
      chrome(captionHtml(c), out, 1920, 1080, work);
      return { ...c, out };
    });
    const cross = join(work, 'cross.svg');
    writeFileSync(cross, svg(400, giltCross({ scale: 0.95 })));
    const end = join(work, 'end.png');
    chrome(endCardHtml(cross), end, 1920, 1080, work);

    const duration = Number(
      execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', iphone])
    );
    const endAt = duration;
    const total = endAt + 3.5;
    const x = 1920 - 170 - phoneW;
    const y = (1080 - phoneH) / 2;
    const inputs = ['-loop', '1', '-t', String(total), '-i', bg, '-i', iphone, '-loop', '1', '-i', frame, '-loop', '1', '-i', mask];
    captions.forEach((c) => inputs.push('-loop', '1', '-i', c.out));
    inputs.push('-loop', '1', '-i', end);
    const fade = (start, stop) =>
      `fade=t=in:st=${start}:d=0.4:alpha=1,fade=t=out:st=${Math.max(start, stop - 0.4)}:d=0.4:alpha=1`;
    let graph =
      `[1:v]fps=30,scale=${phoneW}:${phoneH}:flags=lanczos,format=rgba[ph];` +
      `[3:v]format=gray,scale=${phoneW}:${phoneH}[m];[ph][m]alphamerge[screen];` +
      `[2:v]format=rgba[fr];[fr][screen]overlay=${bezel}:${bezel}[device];` +
      `[device]fade=t=out:st=${endAt - 0.6}:d=0.6:alpha=1[devf];` +
      `[0:v][devf]overlay=${x - bezel}:${y - bezel}:shortest=0:eof_action=pass[b0];`;
    let last = 'b0';
    captions.forEach((c, i) => {
      const stop = Math.min(c.to, endAt);
      graph += `[${4 + i}:v]format=rgba,${fade(c.from, stop)}[c${i}];[${last}][c${i}]overlay=0:0:enable='between(t,${c.from},${stop})'[b${i + 1}];`;
      last = `b${i + 1}`;
    });
    const endIdx = 4 + captions.length;
    graph += `[${endIdx}:v]format=rgba,fade=t=in:st=${endAt}:d=0.6:alpha=1[end];[${last}][end]overlay=0:0:enable='gte(t,${endAt})',format=yuv420p[v]`;
    ffmpeg([
      ...inputs,
      ...SILENCE,
      '-filter_complex', graph,
      '-map', '[v]', '-map', `${endIdx + 1}:a`,
      '-t', String(total), '-r', '30',
      '-c:v', 'libx264', '-profile:v', 'high', '-preset', 'slow', '-crf', '18',
      '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart',
      join(VIDEO, 'promo-1920x1080.mp4'),
    ]);
  } finally {
    rmSync(work, { recursive: true, force: true });
  }
}

mkdirSync(VIDEO, { recursive: true });
await previews();
await promo();
console.log('Videos written to store/video/.');
