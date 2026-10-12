<template>
  <Teleport to="body">
    <Transition :name="`ui-sheet-${resolvedSide}`" appear>
      <div
        v-if="open"
        class="ui-sheet-root"
        :class="`ui-sheet-root--${resolvedSide}`"
        @keydown.esc.stop="close"
      >
        <div class="ui-sheet-scrim" aria-hidden="true" @click="close" />
        <section
          ref="panel"
          class="ui-sheet"
          :class="[`ui-sheet--${resolvedSide}`, `ui-sheet--${size}`]"
          role="dialog"
          aria-modal="true"
          :aria-labelledby="title ? titleId : null"
          :aria-label="title ? null : ariaLabel"
          tabindex="-1"
        >
          <span
            v-if="resolvedSide === 'bottom'"
            class="ui-sheet__grabber"
            aria-hidden="true"
          />
          <header v-if="title || $slots.header" class="ui-sheet__header">
            <slot name="header">
              <div class="ui-sheet__titles">
                <p v-if="eyebrow" class="eyebrow">{{ eyebrow }}</p>
                <h2 :id="titleId" class="ui-sheet__title">{{ title }}</h2>
                <p v-if="subtitle" class="ui-sheet__subtitle">
                  {{ subtitle }}
                </p>
              </div>
            </slot>
            <button
              type="button"
              class="ui-sheet__close"
              aria-label="Close"
              @click="close"
            >
              <UiIcon name="close" />
            </button>
          </header>
          <div class="ui-sheet__body">
            <slot />
          </div>
          <footer v-if="$slots.footer" class="ui-sheet__footer">
            <slot name="footer" />
          </footer>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<script>
// Shared across every sheet so nested sheets lock scroll once and Escape only
// closes the top-most one.
let openCount = 0;

function lockScroll() {
  if (openCount === 0 && typeof document !== 'undefined') {
    document.documentElement.classList.add('has-open-sheet');
  }
  openCount += 1;
}

function unlockScroll() {
  openCount = Math.max(0, openCount - 1);
  if (openCount === 0 && typeof document !== 'undefined') {
    document.documentElement.classList.remove('has-open-sheet');
  }
}
</script>

<script setup>
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  useId,
  watch,
} from 'vue';
import UiIcon from './UiIcon.vue';

/*
  One overlay component for drawers, bottom sheets, and dialogs.
  side:
    'right' | 'left'  drawer
    'bottom'          sheet from the bottom
    'center'          dialog
    'float'           small panel under the header on desktop, bottom sheet on
                      phones (used for quick controls like Display)
    'auto'            right drawer on desktop, bottom sheet on phones
*/
const props = defineProps({
  open: { type: Boolean, default: false },
  side: { type: String, default: 'auto' },
  size: { type: String, default: 'md' },
  title: { type: String, default: '' },
  eyebrow: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  ariaLabel: { type: String, default: null },
});

const emit = defineEmits(['update:open', 'close']);

const panel = ref(null);
const titleId = `ui-sheet-title-${useId()}`;
const isPhone = ref(false);
let media = null;
let previouslyFocused = null;
let locked = false;

const resolvedSide = computed(() => {
  if (props.side === 'auto') return isPhone.value ? 'bottom' : 'right';
  if (props.side === 'float') return isPhone.value ? 'bottom' : 'float';
  return props.side;
});

function close() {
  emit('update:open', false);
  emit('close');
}

function updatePhone() {
  isPhone.value = Boolean(media?.matches);
}

async function onOpened() {
  if (!locked) {
    lockScroll();
    locked = true;
  }
  previouslyFocused = document.activeElement;
  await nextTick();
  const target =
    panel.value?.querySelector('[autofocus]') ||
    panel.value?.querySelector('.ui-sheet__body [tabindex="0"]') ||
    panel.value;
  target?.focus({ preventScroll: true });
}

function onClosed() {
  if (locked) {
    unlockScroll();
    locked = false;
  }
  if (previouslyFocused && typeof previouslyFocused.focus === 'function') {
    previouslyFocused.focus({ preventScroll: true });
  }
  previouslyFocused = null;
}

watch(
  () => props.open,
  (value) => (value ? onOpened() : onClosed())
);

onMounted(() => {
  if (typeof window !== 'undefined' && window.matchMedia) {
    media = window.matchMedia('(max-width: 639px)');
    updatePhone();
    media.addEventListener?.('change', updatePhone);
  }
  if (props.open) onOpened();
});

onBeforeUnmount(() => {
  media?.removeEventListener?.('change', updatePhone);
  if (locked) onClosed();
});
</script>

<style scoped>
.ui-sheet-root {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
}

.ui-sheet-scrim {
  position: absolute;
  inset: 0;
  background-color: var(--scrim);
  backdrop-filter: blur(1.5px);
}

.ui-sheet {
  position: relative;
  display: flex;
  flex-direction: column;
  max-height: 100%;
  background-color: var(--paper);
  color: var(--ink);
  box-shadow: var(--shadow-lg);
  outline: none;
}

.ui-sheet__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-4) var(--space-3) var(--space-5);
  border-bottom: 1px solid var(--rule);
}

.ui-sheet__titles {
  min-width: 0;
  padding-top: var(--space-1);
}

.ui-sheet__title {
  font-size: var(--text-lg);
  font-weight: 400;
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
  line-height: 1.2;
}

.ui-sheet__subtitle {
  margin-top: var(--space-1);
  font-size: var(--text-sm);
  font-style: italic;
  color: var(--ink-soft);
}

.ui-sheet__close {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  color: var(--ink-soft);
  font-size: 1.15rem;
  transition: background-color var(--duration) var(--ease);
}

.ui-sheet__close:hover {
  background-color: var(--paper-sunken);
  color: var(--ink);
}

.ui-sheet__body {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  overscroll-behavior: contain;
  padding: var(--space-5);
}

.ui-sheet__footer {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-5);
  padding-bottom: calc(var(--space-3) + env(safe-area-inset-bottom));
  border-top: 1px solid var(--rule);
}

/* Right / left drawers */
.ui-sheet-root--right {
  justify-content: flex-end;
}

.ui-sheet--right,
.ui-sheet--left {
  height: 100%;
  width: min(100%, 26rem);
  padding-top: env(safe-area-inset-top);
  padding-bottom: env(safe-area-inset-bottom);
}

.ui-sheet--right.ui-sheet--lg,
.ui-sheet--left.ui-sheet--lg {
  width: min(100%, 36rem);
}

.ui-sheet--right.ui-sheet--sm,
.ui-sheet--left.ui-sheet--sm {
  width: min(100%, 21rem);
}

.ui-sheet--right {
  border-left: 1px solid var(--rule);
}

.ui-sheet--left {
  border-right: 1px solid var(--rule);
}

/* Bottom sheet */
.ui-sheet-root--bottom {
  align-items: flex-end;
}

.ui-sheet--bottom {
  width: 100%;
  max-height: calc(var(--vvh) - env(safe-area-inset-top) - 2.5rem);
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  padding-bottom: env(safe-area-inset-bottom);
}

.ui-sheet__grabber {
  align-self: center;
  width: 2.5rem;
  height: 4px;
  margin-top: var(--space-2);
  border-radius: 2px;
  background-color: var(--rule-strong);
}

.ui-sheet--bottom .ui-sheet__header {
  padding-top: var(--space-2);
}

/* Center dialog */
.ui-sheet-root--center {
  align-items: center;
  justify-content: center;
  padding: var(--space-4);
}

.ui-sheet--center {
  width: min(100%, 30rem);
  max-height: calc(var(--vvh) - 2rem);
  border: 1px solid var(--rule);
  border-radius: var(--radius-lg);
}

.ui-sheet--center.ui-sheet--lg {
  width: min(100%, 42rem);
}

/* Float: a compact panel tucked under the header */
.ui-sheet-root--float .ui-sheet-scrim {
  background-color: transparent;
  backdrop-filter: none;
}

.ui-sheet--float {
  position: absolute;
  top: calc(var(--header-height) + env(safe-area-inset-top) + 0.5rem);
  right: max(
    var(--gutter),
    calc((100vw - var(--page-width)) / 2 + var(--gutter))
  );
  width: 23rem;
  max-height: calc(var(--vvh) - var(--header-height) - 2rem);
  border: 1px solid var(--rule);
  border-radius: var(--radius-lg);
}

.ui-sheet--float .ui-sheet__body {
  padding: var(--space-4);
}

/* Transitions */
.ui-sheet-right-enter-active,
.ui-sheet-right-leave-active,
.ui-sheet-left-enter-active,
.ui-sheet-left-leave-active,
.ui-sheet-bottom-enter-active,
.ui-sheet-bottom-leave-active,
.ui-sheet-center-enter-active,
.ui-sheet-center-leave-active,
.ui-sheet-float-enter-active,
.ui-sheet-float-leave-active {
  transition: opacity 220ms var(--ease);
}

.ui-sheet-right-enter-active .ui-sheet,
.ui-sheet-right-leave-active .ui-sheet,
.ui-sheet-left-enter-active .ui-sheet,
.ui-sheet-left-leave-active .ui-sheet,
.ui-sheet-bottom-enter-active .ui-sheet,
.ui-sheet-bottom-leave-active .ui-sheet,
.ui-sheet-center-enter-active .ui-sheet,
.ui-sheet-center-leave-active .ui-sheet,
.ui-sheet-float-enter-active .ui-sheet,
.ui-sheet-float-leave-active .ui-sheet {
  transition: transform 260ms var(--ease);
}

.ui-sheet-right-enter-from,
.ui-sheet-right-leave-to,
.ui-sheet-left-enter-from,
.ui-sheet-left-leave-to,
.ui-sheet-bottom-enter-from,
.ui-sheet-bottom-leave-to,
.ui-sheet-center-enter-from,
.ui-sheet-center-leave-to,
.ui-sheet-float-enter-from,
.ui-sheet-float-leave-to {
  opacity: 0;
}

.ui-sheet-right-enter-from .ui-sheet,
.ui-sheet-right-leave-to .ui-sheet {
  transform: translateX(100%);
}

.ui-sheet-left-enter-from .ui-sheet,
.ui-sheet-left-leave-to .ui-sheet {
  transform: translateX(-100%);
}

.ui-sheet-bottom-enter-from .ui-sheet,
.ui-sheet-bottom-leave-to .ui-sheet {
  transform: translateY(100%);
}

.ui-sheet-center-enter-from .ui-sheet,
.ui-sheet-center-leave-to .ui-sheet {
  transform: translateY(8px) scale(0.98);
}

.ui-sheet-float-enter-from .ui-sheet,
.ui-sheet-float-leave-to .ui-sheet {
  transform: translateY(-6px);
}
</style>

<style>
html.has-open-sheet,
html.has-open-sheet body {
  overflow: hidden;
}
</style>
