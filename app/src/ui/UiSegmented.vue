<template>
  <div
    ref="root"
    role="radiogroup"
    class="ui-segmented"
    :class="[
      `ui-segmented--${variant}`,
      `ui-segmented--${size}`,
      { 'ui-segmented--block': block },
    ]"
    :aria-label="ariaLabel"
  >
    <button
      v-for="(option, index) in options"
      :key="option.value"
      type="button"
      role="radio"
      class="ui-segmented__option"
      :class="{ 'is-selected': option.value === modelValue }"
      :aria-checked="option.value === modelValue ? 'true' : 'false'"
      :tabindex="tabIndexFor(option, index)"
      :title="option.title || null"
      :style="option.style || null"
      @click="select(option)"
      @keydown="onKeydown($event, index)"
    >
      <UiIcon
        v-if="option.icon"
        :name="option.icon"
        class="ui-segmented__icon"
      />
      <span class="ui-segmented__label">
        <slot name="option" :option="option">{{ option.label }}</slot>
      </span>
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import UiIcon from './UiIcon.vue';

/*
  A single choice from a short list, shown all at once.
  options: [{ value, label, icon?, title?, style? }]
  variant: 'pill' (default) | 'underline' (tabs)
*/
const props = defineProps({
  modelValue: { type: [String, Number, Boolean], default: null },
  options: { type: Array, required: true },
  variant: { type: String, default: 'pill' },
  size: { type: String, default: 'md' },
  block: { type: Boolean, default: false },
  ariaLabel: { type: String, default: null },
});

const emit = defineEmits(['update:modelValue', 'change']);
const root = ref(null);

function select(option) {
  if (option.value === props.modelValue) return;
  emit('update:modelValue', option.value);
  emit('change', option.value);
}

function tabIndexFor(option, index) {
  const hasSelection = props.options.some((o) => o.value === props.modelValue);
  if (!hasSelection) return index === 0 ? 0 : -1;
  return option.value === props.modelValue ? 0 : -1;
}

function onKeydown(event, index) {
  const keys = {
    ArrowRight: 1,
    ArrowDown: 1,
    ArrowLeft: -1,
    ArrowUp: -1,
  };
  if (!(event.key in keys)) return;
  event.preventDefault();
  const count = props.options.length;
  const next = (index + keys[event.key] + count) % count;
  select(props.options[next]);
  root.value?.querySelectorAll('button')[next]?.focus();
}
</script>

<style scoped>
.ui-segmented {
  display: inline-flex;
  align-items: stretch;
  max-width: 100%;
}

.ui-segmented--block {
  display: flex;
  width: 100%;
}

.ui-segmented--block .ui-segmented__option {
  flex: 1 1 0;
}

.ui-segmented__option {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.45em;
  min-width: 0;
  font-family: var(--font-book);
  color: var(--ink-soft);
  white-space: nowrap;
  transition:
    background-color var(--duration) var(--ease),
    color var(--duration) var(--ease),
    border-color var(--duration) var(--ease),
    box-shadow var(--duration) var(--ease);
}

.ui-segmented__label {
  overflow: hidden;
  text-overflow: ellipsis;
  padding-top: 0.08em;
}

.ui-segmented__option:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

/* Pill: a recessed track with a raised selection */
.ui-segmented--pill {
  padding: 3px;
  gap: 2px;
  background-color: var(--paper-sunken);
  border: 1px solid var(--rule);
  border-radius: var(--radius);
}

.ui-segmented--pill .ui-segmented__option {
  min-height: 2.5rem;
  padding: 0.25rem 0.85rem;
  border-radius: calc(var(--radius) - 3px);
  font-size: var(--text-sm);
}

.ui-segmented--pill .ui-segmented__option:hover {
  color: var(--ink);
}

.ui-segmented--pill .ui-segmented__option.is-selected {
  background-color: var(--paper-raised);
  color: var(--ink);
  box-shadow:
    var(--shadow-sm),
    0 0 0 1px var(--rule);
}

.ui-segmented--pill.ui-segmented--sm .ui-segmented__option {
  min-height: 2.125rem;
  padding: 0.15rem 0.6rem;
  font-size: var(--text-xs);
}

.ui-segmented--pill.ui-segmented--lg .ui-segmented__option {
  min-height: 2.75rem;
  font-size: var(--text-md);
}

/* Equal-width options leave less room each, so trim their padding. */
.ui-segmented--block.ui-segmented--pill .ui-segmented__option {
  padding-inline: 0.35rem;
  gap: 0.35em;
}

/* Underline: tabs */
.ui-segmented--underline {
  gap: var(--space-1);
  border-bottom: 1px solid var(--rule);
}

.ui-segmented--underline .ui-segmented__option {
  position: relative;
  min-height: 2.75rem;
  padding: 0.35rem 0.75rem;
  font-size: var(--text-md);
}

.ui-segmented--underline .ui-segmented__option::after {
  content: '';
  position: absolute;
  left: 0.5rem;
  right: 0.5rem;
  bottom: -1px;
  height: 2px;
  border-radius: 2px;
  background-color: transparent;
  transition: background-color var(--duration) var(--ease);
}

.ui-segmented--underline .ui-segmented__option:hover {
  color: var(--ink);
}

.ui-segmented--underline .ui-segmented__option.is-selected {
  color: var(--ink);
}

.ui-segmented--underline .ui-segmented__option.is-selected::after {
  background-color: var(--accent);
}

.ui-segmented__icon {
  font-size: 0.95em;
}
</style>
