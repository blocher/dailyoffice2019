/* global setTimeout, scrollY, scrollTo, KeyboardEvent */
// The store tour for the app previews and the promo (store/scripts/build-videos.mjs):
// the office, the psalms and lessons, audio with word highlighting, the
// Offline panel, and Book view, in about 29 seconds. Run it in the app with
//   curl localhost:9999/run --data-binary @store/scripts/remote/tour.js
// while the simulator records (see RELEASE_GUIDE.md).
async function tour() {
  const wait = (ms) => new Promise((r) => setTimeout(r, ms));
  const router =
    document.querySelector('#app').__vue_app__.config.globalProperties.$router;
  const t0 = Date.now();
  const at = async (s) => {
    const d = t0 + s * 1000 - Date.now();
    if (d > 0) await wait(d);
  };
  const smooth = async (to, ms) => {
    const from = scrollY;
    const start = Date.now();
    while (Date.now() - start < ms) {
      const k = (Date.now() - start) / ms;
      const e = k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
      scrollTo(0, from + (to - from) * e);
      await wait(16);
    }
    scrollTo(0, to);
  };
  // 0–4 s: the office
  await at(3.5);
  // 4–9 s: everything in order — scroll through to the psalm
  const psalm = [
    ...document.querySelectorAll('h2, h3, .office-heading, [class*=heading]'),
  ].find((h) => /psalm/i.test(h.innerText));
  await smooth(
    psalm ? psalm.getBoundingClientRect().top + scrollY - 120 : 2400,
    4500
  );
  await at(9.2);
  // 9–15 s: audio, picking up at the Confession (pre-rolled before recording)
  const confession = [
    ...document.querySelectorAll('h2, h3, [class*=heading]'),
  ].find((h) => /confession of sin/i.test(h.innerText));
  await smooth(
    confession ? confession.getBoundingClientRect().top + scrollY - 110 : 0,
    700
  );
  document.querySelector('[aria-label="Play audio"]')?.click();
  await at(15.4);
  document.querySelector('[aria-label="Pause audio"]')?.click();
  // 15.5–21 s: offline
  await router.push('/office/morning_prayer/2026/11/1?panel=offline');
  await at(21.2);
  document.querySelector('.ui-sheet__close')?.click();
  await wait(500);
  // 21.7–29 s: Book view
  await router.push('/office/morning_prayer/2026/11/1?book=1');
  await at(24.5);
  for (let i = 0; i < 3; i++) {
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight' }));
    await wait(1300);
  }
  await at(29);
  return 'done ' + ((Date.now() - t0) / 1000).toFixed(1);
}

await tour();
