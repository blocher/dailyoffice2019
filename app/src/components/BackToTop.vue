<template>
  <Transition name="back-to-top">
    <button
      v-if="visible"
      type="button"
      class="back-to-top"
      :style="{ '--back-to-top-offset': `${offset}px` }"
      aria-label="Back to top"
      @click="toTop"
    >
      <UiIcon name="arrow-up" />
    </button>
  </Transition>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue';

/*
  A quiet way back to the top of a long page. It shows only well down the
  page and while scrolling up, alongside the header, and sits above the
  audio bar when that is showing.
*/
defineProps({
  // Height of anything fixed along the bottom (the audio bar), in px.
  offset: { type: Number, default: 0 },
});

const visible = ref(false);
let lastY = 0;

function onScroll() {
  const y = window.scrollY || document.documentElement.scrollTop || 0;
  if (y < window.innerHeight * 2) {
    visible.value = false;
  } else if (Math.abs(y - lastY) > 6) {
    visible.value = y < lastY;
  }
  lastY = y;
}

function toTop() {
  const reduce = window.matchMedia?.(
    '(prefers-reduced-motion: reduce)'
  ).matches;
  window.scrollTo({ top: 0, behavior: reduce ? 'auto' : 'smooth' });
  document.getElementById('content')?.focus({ preventScroll: true });
}

onMounted(() => window.addEventListener('scroll', onScroll, { passive: true }));
onBeforeUnmount(() => window.removeEventListener('scroll', onScroll));
</script>

<style scoped>
.back-to-top {
  position: fixed;
  right: calc(var(--space-4) + env(safe-area-inset-right));
  bottom: calc(
    var(--space-4) + var(--back-to-top-offset) + env(safe-area-inset-bottom)
  );
  z-index: 90;
  display: grid;
  place-items: center;
  width: 2.75rem;
  height: 2.75rem;
  border: 1px solid var(--rule);
  border-radius: 50%;
  background-color: var(--paper-overlay);
  backdrop-filter: saturate(1.2) blur(10px);
  -webkit-backdrop-filter: saturate(1.2) blur(10px);
  box-shadow: var(--shadow-sm);
  color: var(--ink-soft);
}

.back-to-top:hover {
  color: var(--accent);
  border-color: var(--rule-strong);
}

.back-to-top-enter-active,
.back-to-top-leave-active {
  transition:
    opacity var(--duration) var(--ease),
    transform var(--duration) var(--ease);
}

.back-to-top-enter-from,
.back-to-top-leave-to {
  opacity: 0;
  transform: translateY(0.5rem);
}
</style>
