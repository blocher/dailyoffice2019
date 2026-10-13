<template>
  <div class="size-control">
    <button
      type="button"
      class="size-control__step size-control__step--small"
      aria-label="Smaller text"
      :disabled="state.fontSize <= sizes[0]"
      @click="stepFontSize(-1)"
    >
      A
    </button>
    <div class="size-control__track" role="group" aria-label="Text size">
      <button
        v-for="size in sizes"
        :key="size"
        type="button"
        class="size-control__notch"
        :class="{
          'is-active': size === nearestSize,
          'is-default': size === defaultSize,
        }"
        :aria-label="`${Math.round((size / defaultSize) * 100)}%`"
        :aria-pressed="size === nearestSize ? 'true' : 'false'"
        @click="setFontSize(size)"
      />
    </div>
    <button
      type="button"
      class="size-control__step size-control__step--large"
      aria-label="Larger text"
      :disabled="state.fontSize >= sizes[sizes.length - 1]"
      @click="stepFontSize(1)"
    >
      A
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import {
  DEFAULT_FONT_SIZE,
  FONT_SIZES,
  displayState as state,
  setFontSize,
  stepFontSize,
} from '@/helpers/displayPreferences';

/*
  A ·····•····· A — the reading text size, in fixed notches. Shared by the
  Display panel and the "Make it yours" card.
*/
const sizes = FONT_SIZES;
const defaultSize = DEFAULT_FONT_SIZE;

const nearestSize = computed(() =>
  sizes.reduce((best, size) =>
    Math.abs(size - state.fontSize) < Math.abs(best - state.fontSize)
      ? size
      : best
  )
);
</script>

<style scoped>
/* Text size: A ·····•····· A */
.size-control {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.size-control__step {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 2.75rem;
  height: 2.75rem;
  border: 1px solid var(--rule-strong);
  border-radius: var(--radius);
  background-color: var(--paper-raised);
  color: var(--ink);
  line-height: 1;
}

.size-control__step:hover:not(:disabled) {
  border-color: var(--ink-faint);
}

.size-control__step:disabled {
  opacity: 0.4;
}

.size-control__step--small {
  font-size: 0.95rem;
}

.size-control__step--large {
  font-size: 1.5rem;
}

.size-control__track {
  position: relative;
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 2.75rem;
}

.size-control__track::before {
  content: '';
  position: absolute;
  left: 0.4rem;
  right: 0.4rem;
  top: 50%;
  border-top: 1px solid var(--rule-strong);
}

.size-control__notch {
  position: relative;
  flex: 1 1 0;
  min-width: 0;
  height: 2.75rem;
  display: grid;
  place-items: center;
}

.size-control__notch::after {
  content: '';
  width: 0.45rem;
  height: 0.45rem;
  border-radius: 50%;
  background-color: var(--paper);
  border: 1px solid var(--rule-strong);
  transition:
    transform var(--duration) var(--ease),
    background-color var(--duration) var(--ease);
}

.size-control__notch.is-default::after {
  border-color: var(--ink-faint);
}

.size-control__notch.is-active::after {
  width: 0.95rem;
  height: 0.95rem;
  background-color: var(--accent);
  border-color: var(--accent);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 18%, transparent);
}

.size-control__notch:focus-visible {
  outline: none;
}

.size-control__notch:focus-visible::after {
  box-shadow: var(--focus-ring);
}
</style>
