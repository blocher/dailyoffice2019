<template>
  <Teleport to="body">
    <Transition name="reader">
      <div
        v-if="open"
        ref="root"
        class="reader"
        :class="{
          'is-phone': layout.isPhone,
          'is-spread': layout.spread,
          'has-chrome': chrome,
          'is-turning': turning,
        }"
        :style="cssVars"
        role="dialog"
        aria-modal="true"
        :aria-label="`${title} — book view`"
      >
        <div
          ref="stage"
          class="reader__stage"
          @pointerdown="onPointerDown"
          @pointermove="onPointerMove"
          @pointerup="onPointerUp"
          @pointercancel="onPointerCancel"
          @wheel="onWheel"
          @click.capture="onClickCapture"
        >
          <div class="reader__book" :style="bookStyle">
            <div
              v-for="(page, slot) in pagesOnView"
              :key="slot"
              class="reader__sheet"
              :class="sheetSideClass(slot)"
              :style="{ left: `${slot * layout.sheetW}px` }"
            >
              <p class="reader__head" aria-hidden="true">
                {{ page < totalPages ? sectionTitle(page) : '' }}
              </p>
              <p class="reader__number" aria-hidden="true">
                {{ page < totalPages ? page + 1 : '' }}
              </p>
            </div>

            <div class="reader__window" :class="{ 'is-hidden': sceneActive }">
              <div
                ref="flow"
                class="reader__flow book"
                :style="{ transform: `translateX(${flowOffset}px)` }"
              >
                <header v-if="showTitle" class="reader-title">
                  <p v-if="subtitle" class="reader-title__eyebrow">
                    {{ subtitle }}
                  </p>
                  <h1 class="reader-title__name">{{ title }}</h1>
                  <p v-if="feast" class="reader-title__feast" v-html="feast" />
                  <p class="reader-title__ornament">
                    <Ornament glyph="o" />
                  </p>
                </header>
                <slot />
              </div>
            </div>

            <div
              ref="scene"
              class="reader__scene"
              :class="{ 'is-active': sceneActive }"
              aria-hidden="true"
            />
          </div>
        </div>

        <!-- Toolbars: shown by tapping the middle of the page -->
        <header class="reader__bar reader__bar--top">
          <button
            type="button"
            class="reader__icon-button"
            aria-label="Close book view"
            @click="close()"
          >
            <UiIcon name="close" />
          </button>
          <div class="reader__titles">
            <p class="reader__bar-eyebrow">{{ subtitle }}</p>
            <p class="reader__bar-title">{{ title }}</p>
          </div>
          <button
            type="button"
            class="reader__icon-button reader__aa"
            aria-label="Display: theme, text size, typeface"
            @click="openPanel('display')"
          >
            Aa
          </button>
          <button
            type="button"
            class="reader__icon-button"
            aria-label="Book view options"
            @click="optionsOpen = true"
          >
            <UiIcon name="sliders" />
          </button>
        </header>

        <footer class="reader__bar reader__bar--bottom">
          <p class="reader__section">
            {{ currentSection ? currentSection.title : title }}
          </p>
          <input
            class="ui-range reader__scrubber"
            type="range"
            min="1"
            :max="viewCount"
            :value="view + 1"
            aria-label="Go to page"
            :aria-valuetext="pageLabel"
            @input="goToView(Number($event.target.value) - 1)"
          />
          <p class="reader__progress">
            <span>{{ pageLabel }}</span>
            <span class="reader__left">{{ leftLabel }}</span>
          </p>
        </footer>

        <div
          v-if="hint"
          class="reader__hint"
          @pointerdown.stop
          @click="dismissHint"
        >
          <div class="reader__hint-zone">
            <UiIcon name="chevron-left" />
            <span>Previous page</span>
          </div>
          <div class="reader__hint-zone reader__hint-zone--middle">
            <UiIcon name="menu" />
            <span>Show controls</span>
          </div>
          <div class="reader__hint-zone">
            <UiIcon name="chevron-right" />
            <span>Next page</span>
          </div>
          <p class="reader__hint-note">
            Tap the edges or swipe to turn the page.
          </p>
        </div>

        <p class="visually-hidden" aria-live="polite">{{ pageLabel }}</p>
      </div>
    </Transition>
  </Teleport>

  <UiSheet
    :open="optionsOpen"
    side="float"
    title="Book view"
    @update:open="(value) => (optionsOpen = value)"
  >
    <div class="reader-options">
      <section>
        <h3 class="reader-options__label">Page turn</h3>
        <UiSegmented
          :model-value="turnStyle"
          :options="turnOptions"
          block
          aria-label="Page turn"
          @update:model-value="setTurnStyle"
        />
      </section>
      <section>
        <h3 class="reader-options__label">Pages</h3>
        <UiSegmented
          :model-value="spreadPref"
          :options="spreadOptions"
          block
          aria-label="Pages on screen"
          @update:model-value="setSpreadPref"
        />
        <p class="reader-options__note">
          Two pages show side by side when the screen is wide enough.
        </p>
      </section>
      <section v-if="canFullscreen">
        <UiButton icon="external" block @click="toggleFullscreen">
          {{ isFullscreen ? 'Leave full screen' : 'Full screen' }}
        </UiButton>
      </section>
    </div>
  </UiSheet>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, reactive, ref, watch } from 'vue';
import { displayState } from '@/helpers/displayPreferences';
import { openPanel, panels } from '@/helpers/panels';
import {
  computeReaderLayout,
  countPages,
  countViews,
  pageOfOffset,
  pagesLeftInSection,
  sectionForPage,
  viewOfPage,
} from '@/helpers/readerLayout';
import { DynamicStorage } from '@/helpers/storage';

/*
  Book view: the office laid out as pages, like an e-reader.
    - The text flows into CSS columns one page wide (two on wide screens).
    - Tap the right third or swipe left for the next page, the left third or
      swipe right for the previous one; tap the middle for the toolbars.
    - Arrow keys, Page Up/Down, Space, Home/End, and a trackpad swipe work too.
    - Turning animates as a page lifting on its spine and follows the finger
      while dragging. "Slide" and "None" are available in the options.
*/
const props = defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  feast: { type: String, default: '' },
  // Turn off when the text opens with its own title.
  showTitle: { type: Boolean, default: true },
});
const emit = defineEmits(['update:open']);

const root = ref(null);
const stage = ref(null);
const flow = ref(null);
const scene = ref(null);

const layout = reactive(
  computeReaderLayout({ width: 375, height: 700, fontSize: 24 })
);
const totalPages = ref(1);
const view = ref(0);
const sections = ref([]);
const chrome = ref(false);
const hint = ref(false);
const optionsOpen = ref(false);
const turnStyle = ref('turn');
const spreadPref = ref('auto');
const dragOffset = ref(0);
const sceneActive = ref(false);
const turning = ref(false);
const isFullscreen = ref(false);

const turnOptions = [
  { value: 'turn', label: 'Turn' },
  { value: 'slide', label: 'Slide' },
  { value: 'none', label: 'None' },
];
const spreadOptions = [
  { value: 'auto', label: 'Auto' },
  { value: 'single', label: 'One' },
  { value: 'spread', label: 'Two' },
];

const canFullscreen =
  typeof document !== 'undefined' && Boolean(document.fullscreenEnabled);

const prefersReducedMotion =
  typeof window !== 'undefined' &&
  window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

const viewCount = computed(() => countViews(totalPages.value, layout));
const firstPage = computed(() => view.value * layout.cols);
const pagesOnView = computed(() =>
  Array.from({ length: layout.cols }, (_, i) => firstPage.value + i)
);
const currentSection = computed(() => sectionOn(firstPage.value));
const flowOffset = computed(
  () => -firstPage.value * layout.step + dragOffset.value
);

const pageLabel = computed(() => {
  const last = Math.min(totalPages.value, firstPage.value + layout.cols);
  const range =
    last > firstPage.value + 1
      ? `Pages ${firstPage.value + 1}–${last}`
      : `Page ${firstPage.value + 1}`;
  return `${range} of ${totalPages.value}`;
});

const leftLabel = computed(() => {
  const lastShown = Math.min(
    totalPages.value - 1,
    firstPage.value + layout.cols - 1
  );
  const left = pagesLeftInSection(lastShown, sections.value, totalPages.value);
  if (!sections.value.length) return '';
  if (left === 0) return 'Last page of this section';
  return `${left} ${left === 1 ? 'page' : 'pages'} left in this section`;
});

const cssVars = computed(() => ({
  '--sheet-w': `${layout.sheetW}px`,
  '--sheet-h': `${layout.sheetH}px`,
  '--page-w': `${layout.pageW}px`,
  '--page-h': `${layout.pageH}px`,
  '--pad-x': `${layout.padX}px`,
  '--pad-top': `${layout.padTop}px`,
  '--pad-bottom': `${layout.padBottom}px`,
  '--gap': `${layout.gap}px`,
  '--cols': layout.cols,
  '--window-w': `${layout.windowW}px`,
}));

const bookStyle = computed(() => ({
  width: `${layout.sheetW * layout.cols}px`,
  height: `${layout.sheetH}px`,
}));

function sheetSideClass(slot) {
  if (layout.cols === 1) return 'reader__sheet--single';
  return slot === 0 ? 'reader__sheet--left' : 'reader__sheet--right';
}

// Running head: the first section that begins on the page, otherwise the
// one carried over from earlier pages.
function sectionOn(page) {
  return (
    sections.value.find((s) => s.page === page) ||
    sectionForPage(page, sections.value)
  );
}

function sectionTitle(page) {
  // Like a chapter opening, the first page has no running head.
  if (page === 0) return '';
  return sectionOn(page)?.title || props.title;
}

/* ── Layout ─────────────────────────────────────────── */

function blocks() {
  return flow.value
    ? [
        ...flow.value.querySelectorAll(
          '.reader-title, h2, h3, h4, h5, p, .row, .officeHTML > *'
        ),
      ]
    : [];
}

// The first block on the current page, so a relayout (rotation, text size)
// keeps the reader in the same place.
function findAnchor() {
  const start = firstPage.value;
  return blocks().find((el) => pageOfOffset(el.offsetLeft, layout) >= start);
}

function readSections() {
  if (!flow.value) return [];
  return [...flow.value.querySelectorAll('h2')]
    .map((heading) => ({
      page: pageOfOffset(heading.offsetLeft, layout),
      title: (heading.textContent || '').trim(),
    }))
    .sort((a, b) => a.page - b.page);
}

let relayoutQueued = false;
// The first block on the current page, captured whenever the page changes,
// before any reflow (text size, typeface, rotation) moves things around.
let anchor = null;

function rememberAnchor() {
  anchor = totalPages.value > 1 ? findAnchor() : null;
}

async function relayout() {
  if (!props.open || !stage.value || !flow.value) return;
  const rect = stage.value.getBoundingClientRect();
  const styles = window.getComputedStyle(stage.value);
  const innerHeight =
    rect.height -
    parseFloat(styles.paddingTop || 0) -
    parseFloat(styles.paddingBottom || 0);
  const fontSize =
    parseFloat(window.getComputedStyle(flow.value).fontSize) ||
    displayState.fontSize;
  Object.assign(
    layout,
    computeReaderLayout({
      width: rect.width,
      height: innerHeight,
      fontSize,
      spread: spreadPref.value,
    })
  );
  await nextTick();
  if (!flow.value) return;
  // The audio player finds lines by data-line-id; keep this copy out of it.
  flow.value
    .querySelectorAll('[data-line-id]')
    .forEach((el) => el.removeAttribute('data-line-id'));
  totalPages.value = countPages(flow.value.scrollWidth, layout);
  sections.value = readSections();
  const page =
    anchor && anchor.isConnected ? pageOfOffset(anchor.offsetLeft, layout) : 0;
  view.value = Math.min(viewCount.value - 1, viewOfPage(page, layout));
}

watch(view, async () => {
  await nextTick();
  if (!turning.value) rememberAnchor();
});

watch(turning, async (value) => {
  if (!value) {
    await nextTick();
    rememberAnchor();
  }
});

function queueRelayout() {
  if (relayoutQueued) return;
  relayoutQueued = true;
  window.setTimeout(async () => {
    relayoutQueued = false;
    await relayout();
  }, 120);
}

/* ── Turning pages ──────────────────────────────────── */

function effectiveStyle() {
  return prefersReducedMotion ? 'none' : turnStyle.value;
}

function canGo(direction) {
  const target = view.value + direction;
  return target >= 0 && target < viewCount.value;
}

function goToView(target) {
  view.value = Math.max(0, Math.min(viewCount.value - 1, target));
}

function animate(from, to, duration, onFrame) {
  return new Promise((resolve) => {
    let done = false;
    const finish = () => {
      if (done) return;
      done = true;
      onFrame(to);
      resolve();
    };
    // Browsers pause animation frames in background tabs; never leave a
    // turn half-finished because of it.
    const fallback = window.setTimeout(finish, duration + 250);
    const start = window.performance.now();
    const ease = (t) => 1 - Math.pow(1 - t, 3);
    const tick = (now) => {
      if (done) return;
      const t = Math.min(1, (now - start) / Math.max(1, duration));
      onFrame(from + (to - from) * ease(t));
      if (t < 1) {
        window.requestAnimationFrame(tick);
      } else {
        window.clearTimeout(fallback);
        finish();
      }
    };
    if (document.hidden) {
      window.clearTimeout(fallback);
      finish();
      return;
    }
    window.requestAnimationFrame(tick);
  });
}

// A page face for the turning scene: a static copy of the text strip,
// shifted to show one page, with that page's running head and number.
function makeFace(page, side) {
  const face = scoped(document.createElement('div'));
  face.className = `reader-face reader-face--${side}`;
  if (page >= 0 && page < totalPages.value && flow.value) {
    const win = scoped(document.createElement('div'));
    win.className = 'reader-face__window';
    const copy = flow.value.cloneNode(true);
    copy.style.transform = `translateX(${-page * layout.step}px)`;
    win.appendChild(copy);
    const head = scoped(document.createElement('p'));
    head.className = 'reader__head';
    head.textContent = sectionTitle(page);
    const number = scoped(document.createElement('p'));
    number.className = 'reader__number';
    number.textContent = String(page + 1);
    face.append(head, number, win);
  } else if (side === 'back') {
    face.classList.add('reader-face--verso');
  }
  return face;
}

// Scoped styles key off the component's data-v attribute, so elements built
// by hand need it too.
function scoped(el) {
  const attr = root.value
    ? [...root.value.attributes].find((a) => a.name.startsWith('data-v-'))
    : null;
  if (attr) el.setAttribute(attr.name, '');
  return el;
}

function place(el, slot) {
  el.style.left = `${slot * layout.sheetW}px`;
  return el;
}

/*
  Build the scene for turning one view forward (+1) or back (-1).
  Returns a function that draws the turn at progress p (0 → 1).
*/
function buildTurn(direction) {
  const host = scene.value;
  host.replaceChildren();
  const cols = layout.cols;
  const first = firstPage.value;
  const spread = cols === 2;

  const turner = scoped(document.createElement('div'));
  turner.className = 'reader-turner';
  let front;
  let back;
  let angle;

  if (!spread) {
    if (direction > 0) {
      host.append(place(makeFace(first + 1, 'single'), 0));
      front = makeFace(first, 'single');
      back = makeFace(-1, 'back');
      turner.style.transformOrigin = 'left center';
      angle = (p) => -180 * p;
    } else {
      host.append(place(makeFace(first, 'single'), 0));
      front = makeFace(first - 1, 'single');
      back = makeFace(-1, 'back');
      turner.style.transformOrigin = 'left center';
      angle = (p) => -180 * (1 - p);
    }
    place(turner, 0);
  } else if (direction > 0) {
    host.append(place(makeFace(first, 'left'), 0));
    host.append(place(makeFace(first + 3, 'right'), 1));
    front = makeFace(first + 1, 'right');
    back = makeFace(first + 2, 'left');
    turner.style.transformOrigin = 'left center';
    place(turner, 1);
    angle = (p) => -180 * p;
  } else {
    host.append(place(makeFace(first - 2, 'left'), 0));
    host.append(place(makeFace(first + 1, 'right'), 1));
    front = makeFace(first, 'left');
    back = makeFace(first - 1, 'right');
    turner.style.transformOrigin = 'right center';
    place(turner, 0);
    angle = (p) => 180 * p;
  }

  front.classList.add('reader-turner__front');
  back.classList.add('reader-turner__back');
  front.style.left = '0px';
  back.style.left = '0px';
  turner.append(front, back);
  host.append(turner);
  sceneActive.value = true;

  return (p) => {
    const a = angle(p);
    turner.style.transform = `rotateY(${a}deg)`;
    // Darkest when the page stands upright off the spine.
    const lift = Math.sin((Math.abs(a) / 180) * Math.PI);
    host.style.setProperty('--lift', lift.toFixed(3));
  };
}

function clearScene() {
  sceneActive.value = false;
  scene.value?.replaceChildren();
}

async function turn(direction, { fromProgress = 0, draw = null } = {}) {
  if (turning.value && !draw) return;
  if (!canGo(direction)) {
    await bounce(direction);
    return;
  }
  const style = effectiveStyle();
  if (style === 'none') {
    goToView(view.value + direction);
    return;
  }
  turning.value = true;
  const viewStep = layout.cols * layout.step;
  if (style === 'slide') {
    const from = dragOffset.value;
    const to = -direction * viewStep;
    await animate(from, to, 320 * (1 - Math.abs(from / viewStep)), (x) => {
      dragOffset.value = x;
    });
    view.value += direction;
    dragOffset.value = 0;
  } else {
    const render = draw || buildTurn(direction);
    await animate(fromProgress, 1, 520 * (1 - fromProgress) + 80, render);
    view.value += direction;
    await nextTick();
    clearScene();
  }
  turning.value = false;
}

async function bounce(direction) {
  if (effectiveStyle() === 'none') return;
  turning.value = true;
  await animate(0, -direction * 18, 120, (x) => (dragOffset.value = x));
  await animate(-direction * 18, 0, 180, (x) => (dragOffset.value = x));
  turning.value = false;
}

function next() {
  turn(1);
}

function prev() {
  turn(-1);
}

/* ── Gestures ───────────────────────────────────────── */

const drag = {
  id: null,
  x: 0,
  y: 0,
  t: 0,
  active: false,
  direction: 0,
  draw: null,
  progress: 0,
  bounce: false,
};

function isInteractive(target) {
  return Boolean(
    target.closest?.('a, button, input, select, textarea, summary, label')
  );
}

function onPointerDown(event) {
  if (event.button !== 0 || turning.value || isInteractive(event.target)) {
    return;
  }
  drag.id = event.pointerId;
  drag.x = event.clientX;
  drag.y = event.clientY;
  drag.t = window.performance.now();
  drag.active = false;
  drag.direction = 0;
  drag.draw = null;
  drag.progress = 0;
  drag.bounce = false;
}

function onPointerMove(event) {
  if (drag.id !== event.pointerId) return;
  const dx = event.clientX - drag.x;
  const dy = event.clientY - drag.y;
  if (!drag.active) {
    if (Math.abs(dx) < 10 || Math.abs(dx) < Math.abs(dy) * 1.2) return;
    drag.active = true;
    drag.direction = dx < 0 ? 1 : -1;
    try {
      stage.value?.setPointerCapture?.(event.pointerId);
    } catch {
      // Capture is a nicety; the drag works without it.
    }
    hideChrome();
    const style = effectiveStyle();
    drag.bounce = !canGo(drag.direction) || style === 'none';
    if (!drag.bounce && style === 'turn') {
      drag.draw = buildTurn(drag.direction);
    }
  }
  const distance = layout.spread ? layout.sheetW * 1.6 : layout.sheetW * 0.9;
  const progress = Math.max(0, Math.min(1, (-dx * drag.direction) / distance));
  drag.progress = progress;
  if (drag.bounce) {
    dragOffset.value = dx * 0.15;
  } else if (drag.draw) {
    drag.draw(progress);
  } else {
    dragOffset.value = dx;
  }
}

async function onPointerUp(event) {
  if (drag.id !== event.pointerId) return;
  drag.id = null;
  const dx = event.clientX - drag.x;
  const elapsed = window.performance.now() - drag.t;
  if (!drag.active) {
    if (Math.abs(dx) < 10 && elapsed < 600) handleTap(event.clientX);
    return;
  }
  // A drag that ends over a link shouldn't follow it.
  suppressClick = true;
  window.setTimeout(() => (suppressClick = false), 0);
  const velocity = (-dx * drag.direction) / Math.max(1, elapsed);
  if (drag.bounce) {
    await animate(dragOffset.value, 0, 180, (x) => (dragOffset.value = x));
    return;
  }
  const complete = drag.progress > 0.3 || velocity > 0.45;
  if (complete) {
    await turn(drag.direction, {
      fromProgress: drag.progress,
      draw: drag.draw,
    });
  } else if (drag.draw) {
    turning.value = true;
    await animate(drag.progress, 0, 260, drag.draw);
    clearScene();
    turning.value = false;
  } else {
    turning.value = true;
    await animate(dragOffset.value, 0, 220, (x) => (dragOffset.value = x));
    turning.value = false;
  }
}

function onPointerCancel() {
  if (drag.id === null) return;
  drag.id = null;
  if (drag.draw) {
    clearScene();
  }
  dragOffset.value = 0;
}

// Swallow the click that follows a drag so links don't fire by accident.
let suppressClick = false;
function onClickCapture(event) {
  if (suppressClick) {
    event.preventDefault();
    event.stopPropagation();
    suppressClick = false;
  }
}

function handleTap(clientX) {
  const selection = window.getSelection?.();
  if (selection && String(selection).trim()) return;
  if (chrome.value) {
    hideChrome();
    return;
  }
  const rect = stage.value.getBoundingClientRect();
  const position = (clientX - rect.left) / rect.width;
  if (position < 0.3) prev();
  else if (position > 0.7) next();
  else chrome.value = true;
}

function hideChrome() {
  chrome.value = false;
}

let wheelTotal = 0;
let wheelLock = false;
function onWheel(event) {
  const delta =
    Math.abs(event.deltaX) > Math.abs(event.deltaY)
      ? event.deltaX
      : event.deltaY;
  event.preventDefault();
  if (wheelLock) return;
  wheelTotal += delta;
  if (Math.abs(wheelTotal) > 60) {
    const direction = wheelTotal > 0 ? 1 : -1;
    wheelTotal = 0;
    wheelLock = true;
    turn(direction).finally(() => {
      window.setTimeout(() => (wheelLock = false), 250);
    });
  }
}

function onKeydown(event) {
  if (!props.open || optionsOpen.value || panels.display) return;
  if (event.target?.matches?.('input, textarea, select')) return;
  const key = event.key;
  if (key === 'Escape') {
    if (chrome.value) hideChrome();
    else close();
  } else if (
    key === 'ArrowRight' ||
    key === 'PageDown' ||
    (key === ' ' && !event.shiftKey)
  ) {
    event.preventDefault();
    next();
  } else if (
    key === 'ArrowLeft' ||
    key === 'PageUp' ||
    (key === ' ' && event.shiftKey)
  ) {
    event.preventDefault();
    prev();
  } else if (key === 'Home') {
    event.preventDefault();
    goToView(0);
  } else if (key === 'End') {
    event.preventDefault();
    goToView(viewCount.value - 1);
  }
}

/* ── Options ────────────────────────────────────────── */

async function setTurnStyle(value) {
  turnStyle.value = value;
  await DynamicStorage.setItem('readerTurnStyle', value);
}

async function setSpreadPref(value) {
  spreadPref.value = value;
  await DynamicStorage.setItem('readerSpread', value);
  await relayout();
}

async function toggleFullscreen() {
  try {
    if (document.fullscreenElement) await document.exitFullscreen();
    else await document.documentElement.requestFullscreen();
  } catch {
    // Not allowed here; nothing to do.
  }
}

function onFullscreenChange() {
  isFullscreen.value = Boolean(document.fullscreenElement);
  queueRelayout();
}

async function dismissHint() {
  hint.value = false;
  await DynamicStorage.setItem('readerHintSeen', 'true');
}

/* ── Open / close ───────────────────────────────────── */

let resizeObserver = null;

// Back (browser, Android gesture) closes the book view instead of leaving
// the office.
function onPopState() {
  if (props.open) {
    historyPushed = false;
    emit('update:open', false);
  }
}

let historyPushed = false;

function close() {
  if (historyPushed && window.history.state?.bookReader) {
    window.history.back();
    return;
  }
  emit('update:open', false);
}

async function onOpen() {
  document.documentElement.classList.add('has-reader');
  const [style, spread, seen] = await Promise.all([
    DynamicStorage.getItem('readerTurnStyle'),
    DynamicStorage.getItem('readerSpread'),
    DynamicStorage.getItem('readerHintSeen'),
  ]);
  if (['turn', 'slide', 'none'].includes(style)) turnStyle.value = style;
  if (['auto', 'single', 'spread'].includes(spread)) spreadPref.value = spread;
  hint.value = seen !== 'true';
  chrome.value = false;
  view.value = 0;
  totalPages.value = 1;
  anchor = null;

  window.history.pushState({ ...window.history.state, bookReader: true }, '');
  historyPushed = true;
  window.addEventListener('popstate', onPopState);
  window.addEventListener('keydown', onKeydown);
  document.addEventListener('fullscreenchange', onFullscreenChange);

  await nextTick();
  await relayout();
  // Fonts can finish loading after the first layout.
  if (document.fonts?.ready) {
    document.fonts.ready.then(() => relayout());
  }
  if (typeof window.ResizeObserver !== 'undefined' && stage.value) {
    resizeObserver = new window.ResizeObserver(queueRelayout);
    resizeObserver.observe(stage.value);
  }
}

function onClose() {
  document.documentElement.classList.remove('has-reader');
  window.removeEventListener('popstate', onPopState);
  window.removeEventListener('keydown', onKeydown);
  document.removeEventListener('fullscreenchange', onFullscreenChange);
  resizeObserver?.disconnect();
  resizeObserver = null;
  optionsOpen.value = false;
  if (document.fullscreenElement) document.exitFullscreen?.();
  if (historyPushed && window.history.state?.bookReader) {
    historyPushed = false;
    window.history.back();
  }
}

watch(
  () => props.open,
  (value) => (value ? onOpen() : onClose()),
  { immediate: true }
);

watch(
  () => [displayState.fontSize, displayState.readingFont],
  async () => {
    await nextTick();
    queueRelayout();
    document.fonts?.ready?.then(() => queueRelayout());
  }
);

onBeforeUnmount(() => {
  if (props.open) onClose();
});
</script>

<style scoped>
.reader {
  --gutter-shade: rgb(0 0 0 / 0.08);
  /* The left margin stays visible for hanging indents and verse numbers */
  --bleed: var(--pad-x);
  position: fixed;
  inset: 0;
  z-index: 900;
  display: flex;
  flex-direction: column;
  background-color: var(--paper-sunken);
  color: var(--ink);
  overscroll-behavior: contain;
}

.reader.is-phone {
  background-color: var(--paper);
}

:root.dark .reader {
  --gutter-shade: rgb(0 0 0 / 0.55);
}

.reader__stage {
  position: relative;
  flex: 1 1 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 0;
  padding-top: env(safe-area-inset-top);
  padding-bottom: env(safe-area-inset-bottom);
  overflow: hidden;
  touch-action: none;
  user-select: none;
  -webkit-user-select: none;
  cursor: default;
}

/* The book: one or two sheets of paper */
.reader__book {
  position: relative;
  flex-shrink: 0;
}

.reader:not(.is-phone) .reader__book {
  box-shadow: var(--shadow-lg);
}

.reader__sheet,
.reader-face {
  position: absolute;
  top: 0;
  width: var(--sheet-w);
  height: var(--sheet-h);
  background-color: var(--paper);
  overflow: hidden;
}

/* The gutter: a soft shadow where pages meet the spine */
.reader__sheet--left,
.reader-face--left {
  background-image: linear-gradient(
    to left,
    var(--gutter-shade),
    transparent 7%
  );
}

.reader__sheet--right,
.reader-face--right {
  background-image: linear-gradient(
    to right,
    var(--gutter-shade),
    transparent 7%
  );
}

/* Running head and folio, as in the printed book */
.reader__head,
.reader__number {
  position: absolute;
  left: var(--pad-x);
  right: var(--pad-x);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: var(--font-book);
  font-size: 0.8125rem;
  font-variant-caps: all-small-caps;
  letter-spacing: 0.14em;
  color: var(--ink-faint);
  text-align: center;
  pointer-events: none;
}

.reader__head {
  top: calc(var(--pad-top) * 0.42);
}

.reader__number {
  bottom: calc(var(--pad-bottom) * 0.36);
  font-variant-numeric: oldstyle-nums;
  letter-spacing: 0.05em;
}

.reader__sheet--left .reader__number,
.reader-face--left .reader__number {
  text-align: left;
}

.reader__sheet--right .reader__number,
.reader-face--right .reader__number {
  text-align: right;
}

/* The text window across the page(s) on screen. It opens into the left
   margin so hanging indents and verse numbers show, and stops at the right
   text edge so the next page never peeks in. */
.reader__window,
.reader-face__window {
  position: absolute;
  top: var(--pad-top);
  left: calc(var(--pad-x) - var(--bleed));
  height: var(--page-h);
  padding-left: var(--bleed);
  overflow: hidden;
}

.reader__window {
  width: calc(var(--window-w) + var(--bleed));
}

.reader__window.is-hidden {
  visibility: hidden;
}

.reader-face__window {
  width: calc(var(--page-w) + var(--bleed));
}

.reader-face__window > .reader__flow {
  position: absolute;
  top: 0;
  left: var(--bleed);
}

/* The text strip: pages are columns */
.reader__flow,
.reader__flow.book {
  position: relative;
  width: var(--window-w);
  max-width: none;
  height: var(--page-h);
  margin: 0;
  padding: 0;
  column-count: var(--cols);
  column-gap: var(--gap);
  column-fill: auto;
}

.reader__flow :deep(h1),
.reader__flow :deep(h2),
.reader__flow :deep(h3),
.reader__flow :deep(h4) {
  break-after: avoid;
  break-inside: avoid;
}

.reader__flow :deep(.row),
.reader__flow :deep(h5),
.reader__flow :deep(img),
.reader__flow :deep(iframe) {
  break-inside: avoid;
}

.reader__flow :deep(p) {
  orphans: 2;
  widows: 2;
}

.reader__flow :deep(img),
.reader__flow :deep(iframe) {
  max-width: 100%;
}

/* Title page block */
.reader-title {
  padding: 0.6em 0 0.4em;
  text-align: center;
  break-inside: avoid;
}

.reader-title__eyebrow {
  font-size: 0.62em;
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
  color: var(--ink-faint);
}

.reader__flow .reader-title__name {
  margin: 0.15em 0 0;
  padding: 0;
  font-size: 1.35em;
  line-height: 1.2;
}

.reader-title__feast {
  margin-top: 0.45em;
  font-size: 0.85em;
  font-style: italic;
  line-height: 1.35;
  color: var(--ink-soft);
}

.reader-title__ornament {
  margin-top: 0.5em;
  font-size: 1.1em;
  line-height: 1;
}

/* The turning scene */
.reader__scene {
  position: absolute;
  inset: 0;
  display: none;
  perspective: 2600px;
  pointer-events: none;
  --lift: 0;
}

.reader__scene.is-active {
  display: block;
}

.reader__scene :deep(.reader-turner) {
  position: absolute;
  top: 0;
  width: var(--sheet-w);
  height: var(--sheet-h);
  transform-style: preserve-3d;
  will-change: transform;
}

.reader__scene :deep(.reader-turner__front),
.reader__scene :deep(.reader-turner__back) {
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
  box-shadow: 0 0 calc(var(--lift) * 40px)
    color-mix(in srgb, #000 calc(var(--lift) * 30%), transparent);
}

.reader__scene :deep(.reader-turner__back) {
  transform: rotateY(180deg);
}

/* Shade the lifting page as it stands up off the spine */
.reader__scene :deep(.reader-turner__front)::after,
.reader__scene :deep(.reader-turner__back)::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: linear-gradient(
    to right,
    color-mix(in srgb, #000 calc(var(--lift) * 14%), transparent),
    transparent 60%
  );
}

/* The plain reverse of a single page */
.reader__scene :deep(.reader-face--verso) {
  background-color: var(--paper-sunken);
}

/* Toolbars */
.reader__bar {
  position: absolute;
  left: 0;
  right: 0;
  z-index: 3;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) max(var(--space-3), env(safe-area-inset-left));
  background-color: var(--paper-overlay);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  transition:
    transform 240ms var(--ease),
    opacity 240ms var(--ease);
}

.reader__bar--top {
  top: 0;
  padding-top: calc(var(--space-2) + env(safe-area-inset-top));
  border-bottom: 1px solid var(--rule);
  transform: translateY(-100%);
  opacity: 0;
}

.reader__bar--bottom {
  bottom: 0;
  flex-direction: column;
  align-items: stretch;
  gap: var(--space-1);
  padding-bottom: calc(var(--space-3) + env(safe-area-inset-bottom));
  border-top: 1px solid var(--rule);
  transform: translateY(100%);
  opacity: 0;
}

.reader__bar {
  pointer-events: none;
}

.reader.has-chrome .reader__bar {
  transform: none;
  opacity: 1;
  pointer-events: auto;
}

.reader__icon-button {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 2.75rem;
  height: 2.75rem;
  border-radius: var(--radius);
  color: var(--ink-soft);
  font-size: 1.2rem;
}

.reader__icon-button:hover {
  background-color: var(--paper-sunken);
  color: var(--ink);
}

.reader__aa {
  font-size: 1.1rem;
  line-height: 1;
}

.reader__titles {
  flex: 1;
  min-width: 0;
  text-align: center;
}

.reader__bar-eyebrow {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: var(--text-xs);
  font-style: italic;
  color: var(--ink-faint);
}

.reader__bar-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-variant-caps: all-small-caps;
  letter-spacing: 0.12em;
}

.reader__section {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: var(--text-sm);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.12em;
  text-align: center;
  color: var(--ink-soft);
}

.reader__scrubber {
  width: min(100%, 40rem);
  align-self: center;
}

.reader__progress {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0 var(--space-3);
  font-size: var(--text-xs);
  color: var(--ink-faint);
}

.reader__left {
  font-style: italic;
}

/* First-run hint */
.reader__hint {
  position: absolute;
  inset: 0;
  z-index: 4;
  display: grid;
  grid-template-columns: 3fr 4fr 3fr;
  background-color: color-mix(in srgb, var(--paper) 72%, transparent);
  backdrop-filter: blur(2px);
  animation: reader-hint-in 300ms var(--ease);
}

.reader__hint-zone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-3);
  border-right: 1px dashed var(--rule-strong);
  font-size: var(--text-sm);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.12em;
  color: var(--ink-soft);
  text-align: center;
}

.reader__hint-zone .ui-icon {
  font-size: 1.6rem;
  color: var(--accent);
}

.reader__hint-zone:last-of-type {
  border-right: 0;
}

.reader__hint-note {
  position: absolute;
  left: 0;
  right: 0;
  bottom: calc(var(--space-6) + env(safe-area-inset-bottom));
  font-size: var(--text-sm);
  font-style: italic;
  text-align: center;
  color: var(--ink-soft);
}

@keyframes reader-hint-in {
  from {
    opacity: 0;
  }
}

/* Opening and closing */
.reader-enter-active,
.reader-leave-active {
  transition: opacity 260ms var(--ease);
}

.reader-enter-active .reader__book,
.reader-leave-active .reader__book {
  transition: transform 320ms var(--ease);
}

.reader-enter-from,
.reader-leave-to {
  opacity: 0;
}

.reader-enter-from .reader__book,
.reader-leave-to .reader__book {
  transform: scale(0.97);
}

/* Options sheet */
.reader-options {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.reader-options__label {
  margin-bottom: var(--space-2);
  font-size: var(--text-md);
  font-weight: 400;
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
}

.reader-options__note {
  margin-top: var(--space-2);
  font-size: var(--text-sm);
  font-style: italic;
  color: var(--ink-faint);
}
</style>

<style>
html.has-reader,
html.has-reader body {
  overflow: hidden;
}
</style>
