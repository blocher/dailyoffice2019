<template>
  <details class="ui-disclosure" :open="open" @toggle="onToggle">
    <summary class="ui-disclosure__summary">
      <span class="ui-disclosure__title">
        <slot name="title">{{ title }}</slot>
      </span>
      <span v-if="$slots.meta || meta" class="ui-disclosure__meta">
        <slot name="meta">{{ meta }}</slot>
      </span>
      <UiIcon name="chevron-down" class="ui-disclosure__chevron" />
    </summary>
    <div class="ui-disclosure__body">
      <slot />
    </div>
  </details>
</template>

<script setup>
import UiIcon from './UiIcon.vue';

/*
  A titled section that folds away. `meta` shows on the right of the title
  (e.g. the current value) so a closed row still tells you what's inside.
*/
defineProps({
  title: { type: String, default: '' },
  meta: { type: String, default: '' },
  open: { type: Boolean, default: false },
});
const emit = defineEmits(['update:open']);

function onToggle(event) {
  emit('update:open', event.target.open);
}
</script>

<style scoped>
.ui-disclosure {
  border-bottom: 1px solid var(--rule);
}

.ui-disclosure__summary {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-height: 3.25rem;
  padding: var(--space-2) var(--space-1);
  list-style: none;
  cursor: pointer;
  user-select: none;
}

.ui-disclosure__summary::-webkit-details-marker {
  display: none;
}

.ui-disclosure__summary:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
  border-radius: var(--radius-sm);
}

.ui-disclosure__title {
  flex: 1 1 auto;
  min-width: 0;
  color: var(--ink);
}

.ui-disclosure__meta {
  flex: 0 1 auto;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 55%;
  font-size: var(--text-sm);
  font-style: italic;
  color: var(--accent);
}

.ui-disclosure__chevron {
  flex-shrink: 0;
  color: var(--ink-faint);
  font-size: 0.85rem;
  transition: transform var(--duration) var(--ease);
}

.ui-disclosure[open] > .ui-disclosure__summary .ui-disclosure__chevron {
  transform: rotate(180deg);
}

.ui-disclosure__body {
  padding: 0 var(--space-1) var(--space-4);
}
</style>
